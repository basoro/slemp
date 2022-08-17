
function str2Obj(str){
    var data = {};
    kv = str.split('&');
    for(i in kv){
        v = kv[i].split('=');
        data[v[0]] = v[1];
    }
    return data;
}

function phpPost(method, version, args,callback){
    var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });

    var req_data = {};
    req_data['name'] = 'php';
    req_data['func'] = method;
    req_data['version'] = version;

    if (typeof(args) == 'string'){
        req_data['args'] = JSON.stringify(str2Obj(args));
    } else {
        req_data['args'] = JSON.stringify(args);
    }

    $.post('/plugins/run', req_data, function(data) {
        layer.close(loadT);
        if (!data.status){
            layer.msg(data.msg,{icon:0,time:2000,shade: [10, '#000']});
            return;
        }

        if(typeof(callback) == 'function'){
            callback(data);
        }
    },'json');
}

function phpPostCallbak(method, version, args,callback){
    var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });

    var req_data = {};
    req_data['name'] = 'php';
    req_data['func'] = method;
    args['version'] = version;

    if (typeof(args) == 'string'){
        req_data['args'] = JSON.stringify(str2Obj(args));
    } else {
        req_data['args'] = JSON.stringify(args);
    }

    $.post('/plugins/callback', req_data, function(data) {
        layer.close(loadT);
        if (!data.status){
            layer.msg(data.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }

        if(typeof(callback) == 'function'){
            callback(data);
        }
    },'json');
}

function phpSetConfig(version) {
    phpPost('get_php_conf', version,'',function(data){
        // console.log(data);
        var rdata = $.parseJSON(data.data);
        // console.log(rdata);
        var mlist = '';
        for (var i = 0; i < rdata.length; i++) {
            var w = '70'
            if (rdata[i].name == 'error_reporting') w = '250';
            var ibody = '<input style="width: ' + w + 'px;" class="bt-input-text mr5" name="' + rdata[i].name + '" value="' + rdata[i].value + '" type="text" >';
            switch (rdata[i].type) {
                case 0:
                    var selected_1 = (rdata[i].value == 1) ? 'selected' : '';
                    var selected_0 = (rdata[i].value == 0) ? 'selected' : '';
                    ibody = '<select class="bt-input-text mr5" name="' + rdata[i].name + '" style="width: ' + w + 'px;"><option value="1" ' + selected_1 + '>Start</option><option value="0" ' + selected_0 + '>Stop</option></select>'
                    break;
                case 1:
                    var selected_1 = (rdata[i].value == 'On') ? 'selected' : '';
                    var selected_0 = (rdata[i].value == 'Off') ? 'selected' : '';
                    ibody = '<select class="bt-input-text mr5" name="' + rdata[i].name + '" style="width: ' + w + 'px;"><option value="On" ' + selected_1 + '>Start</option><option value="Off" ' + selected_0 + '>Stop</option></select>'
                    break;
            }
            mlist += '<p><span>' + rdata[i].name + '</span>' + ibody + ', <font>' + rdata[i].ps + '</font></p>'
        }
        var phpCon = '<style>.conf_p p{margin-bottom: 2px}</style><div class="conf_p" style="margin-bottom:0">\
                        ' + mlist + '\
                        <div style="margin-top:10px; padding-right:15px" class="text-right"><button class="btn btn-success btn-sm mr5" onclick="phpSetConfig(' + version + ')">Refresh</button><button class="btn btn-success btn-sm" onclick="submitConf(' + version + ')">Save</button></div>\
                    </div>'
        $(".soft-man-con").html(phpCon);
    });
}


function submitConf(version) {
    var data = {
        version: version,
        display_errors: $("select[name='display_errors']").val(),
        'cgi.fix_pathinfo': $("select[name='cgi.fix_pathinfo']").val(),
        'date.timezone': $("input[name='date.timezone']").val(),
        short_open_tag: $("select[name='short_open_tag']").val(),
        asp_tags: $("select[name='asp_tags']").val() || 'On',
        safe_mode: $("select[name='safe_mode']").val(),
        max_execution_time: $("input[name='max_execution_time']").val(),
        max_input_time: $("input[name='max_input_time']").val(),
        max_input_vars: $("input[name='max_input_vars']").val(),
        memory_limit: $("input[name='memory_limit']").val(),
        post_max_size: $("input[name='post_max_size']").val(),
        file_uploads: $("select[name='file_uploads']").val(),
        upload_max_filesize: $("input[name='upload_max_filesize']").val(),
        max_file_uploads: $("input[name='max_file_uploads']").val(),
        default_socket_timeout: $("input[name='default_socket_timeout']").val(),
        error_reporting: $("input[name='error_reporting']").val() || 'On'
    };

    phpPost('submit_php_conf', version, data, function(ret_data){
        var rdata = $.parseJSON(ret_data.data);
        // console.log(rdata);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function phpUploadLimitReq(version){
    phpPost('get_limit_conf', version, '', function(ret_data){
        var rdata = $.parseJSON(ret_data.data);
        phpUploadLimit(version,rdata['max']);
    });
}

function phpUploadLimit(version,max){
    var LimitCon = '<p class="conf_p"><input class="phpUploadLimit bt-input-text mr5" type="number" value="'+
    max+'" name="max">MB<button class="btn btn-success btn-sm" onclick="setPHPMaxSize(\''+
    version+'\')" style="margin-left:20px">Save</button></p>';
    $(".soft-man-con").html(LimitCon);
}

function phpTimeLimitReq(version){
    phpPost('get_limit_conf', version, '', function(ret_data){
        var rdata = $.parseJSON(ret_data.data);
        phpTimeLimit(version,rdata['maxTime']);
    });
}

function phpTimeLimit(version, max) {
    var LimitCon = '<p class="conf_p"><input class="phpTimeLimit bt-input-text mr5" type="number" value="' + max + '">second<button class="btn btn-success btn-sm" onclick="setPHPMaxTime(\'' + version + '\')" style="margin-left:20px">Save</button></p>';
    $(".soft-man-con").html(LimitCon);
}

function setPHPMaxTime(version) {
    var max = $(".phpTimeLimit").val();
    phpPost('set_max_time',version,{'time':max},function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function setPHPMaxSize(version) {
    max = $(".phpUploadLimit").val();
    if (max < 2) {
        alert(max);
        layer.msg('Upload size limit cannot be less than 2M', { icon: 2 });
        return;
    }

    phpPost('set_max_size',version,{'max':max},function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function getFpmConfig(version){
    phpPost('get_fpm_conf', version, {}, function(data){
        // console.log(data);
        var rdata = $.parseJSON(data.data);
        // console.log(rdata);
        var limitList = "<option value='0'>Customize</option>" +
            "<option value='1' " + (rdata.max_children == 30 ? 'selected' : '') + ">30 concurrent</option>" +
            "<option value='2' " + (rdata.max_children == 50 ? 'selected' : '') + ">50 concurrent</option>" +
            "<option value='3' " + (rdata.max_children == 100 ? 'selected' : '') + ">100 concurrent</option>" +
            "<option value='4' " + (rdata.max_children == 200 ? 'selected' : '') + ">200 concurrent</option>" +
            "<option value='5' " + (rdata.max_children == 300 ? 'selected' : '') + ">300 concurrent</option>" +
            "<option value='6' " + (rdata.max_children == 500 ? 'selected' : '') + ">500 concurrent</option>"
        var pms = [{ 'name': 'static', 'title': 'Static' }, { 'name': 'dynamic', 'title': 'Dynamic' }];
        var pmList = '';
        for (var i = 0; i < pms.length; i++) {
            pmList += '<option value="' + pms[i].name + '" ' + ((pms[i].name == rdata.pm) ? 'selected' : '') + '>' + pms[i].title + '</option>';
        }
        var body = "<div class='bingfa'>" +
            "<p class='line'><span class='span_tit'>Concurrency scheme：</span><select class='bt-input-text' name='limit' style='width:100px;'>" + limitList + "</select></p>" +
            "<p class='line'><span class='span_tit'>Operating mode：</span><select class='bt-input-text' name='pm' style='width:100px;'>" + pmList + "</select><span class='c9'>*PHP-FPM operating mode</span></p>" +
            "<p class='line'><span class='span_tit'>max_children：</span><input class='bt-input-text' type='number' name='max_children' value='" + rdata.max_children + "' /><span class='c9'>*Maximum number of child processes allowed to be created</span></p>" +
            "<p class='line'><span class='span_tit'>start_servers：</span><input class='bt-input-text' type='number' name='start_servers' value='" + rdata.start_servers + "' />  <span class='c9'>*Number of starting processes (initial number of processes after the service starts)</span></p>" +
            "<p class='line'><span class='span_tit'>min_spare_servers：</span><input class='bt-input-text' type='number' name='min_spare_servers' value='" + rdata.min_spare_servers + "' />   <span class='c9'>*Minimum number of idle processes (number to keep after cleaning up idle processes)</span></p>" +
            "<p class='line'><span class='span_tit'>max_spare_servers：</span><input class='bt-input-text' type='number' name='max_spare_servers' value='" + rdata.max_spare_servers + "' />   <span class='c9'>*Maximum number of idle processes (clean up when idle processes reach this value)</span></p>" +
            "<div class='mtb15'><button class='btn btn-success btn-sm' onclick='setFpmConfig(\"" + version + "\",1)'>Save</button></div>" +
            "</div>";

        $(".soft-man-con").html(body);
        $("select[name='limit']").change(function() {
            var type = $(this).val();
            var max_children = rdata.max_children;
            var start_servers = rdata.start_servers;
            var min_spare_servers = rdata.min_spare_servers;
            var max_spare_servers = rdata.max_spare_servers;
            switch (type) {
                case '1':
                    max_children = 30;
                    start_servers = 5;
                    min_spare_servers = 5;
                    max_spare_servers = 20;
                    break;
                case '2':
                    max_children = 50;
                    start_servers = 15;
                    min_spare_servers = 15;
                    max_spare_servers = 35;
                    break;
                case '3':
                    max_children = 100;
                    start_servers = 20;
                    min_spare_servers = 20;
                    max_spare_servers = 70;
                    break;
                case '4':
                    max_children = 200;
                    start_servers = 25;
                    min_spare_servers = 25;
                    max_spare_servers = 150;
                    break;
                case '5':
                    max_children = 300;
                    start_servers = 30;
                    min_spare_servers = 30;
                    max_spare_servers = 180;
                    break;
                case '6':
                    max_children = 500;
                    start_servers = 35;
                    min_spare_servers = 35;
                    max_spare_servers = 250;
                    break;
            }

            $("input[name='max_children']").val(max_children);
            $("input[name='start_servers']").val(start_servers);
            $("input[name='min_spare_servers']").val(min_spare_servers);
            $("input[name='max_spare_servers']").val(max_spare_servers);
        });
    });
}

function setFpmConfig(version){
    var max_children = Number($("input[name='max_children']").val());
    var start_servers = Number($("input[name='start_servers']").val());
    var min_spare_servers = Number($("input[name='min_spare_servers']").val());
    var max_spare_servers = Number($("input[name='max_spare_servers']").val());
    var pm = $("select[name='pm']").val();

    if (max_children < max_spare_servers) {
        layer.msg('max_spare_servers cannot be greater than max_children', { icon: 2 });
        return;
    }

    if (min_spare_servers > start_servers) {
        layer.msg('min_spare_servers cannot be greater than start_servers', { icon: 2 });
        return;
    }

    if (max_spare_servers < min_spare_servers) {
        layer.msg('min_spare_servers cannot be greater than max_spare_servers', { icon: 2 });
        return;
    }

    if (max_children < start_servers) {
        layer.msg('start_servers cannot be greater than max_children', { icon: 2 });
        return;
    }

    if (max_children < 1 || start_servers < 1 || min_spare_servers < 1 || max_spare_servers < 1) {
        layer.msg('The configuration value cannot be less than 1', { icon: 2 });
        return;
    }

    var data = {
        version:version,
        max_children:max_children,
        start_servers:start_servers,
        min_spare_servers:min_spare_servers,
        max_spare_servers:max_spare_servers,
        pm:pm,
    };
    phpPost('set_fpm_conf', version, data, function(ret_data){
        var rdata = $.parseJSON(ret_data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}


function getFpmStatus(version){
    phpPost('get_fpm_status', version, '', function(ret_data){
        var tmp_data = $.parseJSON(ret_data.data);
        if(!tmp_data.status){
            layer.msg(tmp_data.msg, { icon: tmp_data.status ? 1 : 2 });
            return;
        }

        var rdata = tmp_data.data;
        var con = "<div style='height:420px;overflow:hidden;'><table class='table table-hover table-bordered GetPHPStatus' style='margin:0;padding:0'>\
                        <tr><th>Pool</th><td>" + rdata.pool + "</td></tr>\
                        <tr><th>Process manager</th><td>" + ((rdata['process manager'] == 'dynamic') ? 'dynamic' : 'static') + "</td></tr>\
                        <tr><th>Start time</th><td>" + rdata['start time'] + "</td></tr>\
                        <tr><th>Accepted conn</th><td>" + rdata['accepted conn'] + "</td></tr>\
                        <tr><th>Listen queue</th><td>" + rdata['listen queue'] + "</td></tr>\
                        <tr><th>Max listen queue</th><td>" + rdata['max listen queue'] + "</td></tr>\
                        <tr><th>Listen queue len</th><td>" + rdata['listen queue len'] + "</td></tr>\
                        <tr><th>Idle processes</th><td>" + rdata['idle processes'] + "</td></tr>\
                        <tr><th>Active processes</th><td>" + rdata['active processes'] + "</td></tr>\
                        <tr><th>Total processes</th><td>" + rdata['total processes'] + "</td></tr>\
                        <tr><th>Max active processes</th><td>" + rdata['max active processes'] + "</td></tr>\
                        <tr><th>Max children reached</th><td>" + rdata['max children reached'] + "</td></tr>\
                        <tr><th>Slow requests</th><td>" + rdata['slow requests'] + "</td></tr>\
                     </table></div>";
        $(".soft-man-con").html(con);
        $(".GetPHPStatus td,.GetPHPStatus th").css("padding", "7px");
    });
}

function disableFunc(version) {
    phpPost('get_disable_func', version,'',function(data){
        var rdata = $.parseJSON(data.data);
        var disable_functions = rdata.disable_functions.split(',');
        var dbody = ''
        for (var i = 0; i < disable_functions.length; i++) {
            if (disable_functions[i] == '') continue;
            dbody += "<tr><td>" + disable_functions[i] + "</td><td><a style='float:right;' href=\"javascript:setDisableFunc('" + version + "','" + disable_functions[i] + "','" + rdata.disable_functions + "');\">Delete</a></td></tr>";
        }

        var con = "<div class='dirBinding'>" +
            "<input class='bt-input-text mr5' type='text' placeholder='Add the function name to be forbidden, like: exec' id='disable_function_val' style='height: 28px; border-radius: 3px;width: 410px;' />" +
            "<button class='btn btn-success btn-sm' onclick=\"setDisableFunc('" + version + "',1,'" + rdata.disable_functions + "')\">Add to</button>" +
            "</div>" +
            "<div class='divtable mtb15' style='height:350px;overflow:auto'><table class='table table-hover' width='100%' style='margin-bottom:0'>" +
            "<thead><tr><th>Name</th><th width='100' class='text-right'>Action</th></tr></thead>" +
            "<tbody id='blacktable'>" + dbody + "</tbody>" +
            "</table></div>";

        con += '<ul class="help-info-text">\
                    <li>Here you can disable the invocation of the specified function to enhance environment security!</li>\
                    <li>It is strongly recommended to disable dangerous functions such as exec, system, etc.!</li>\
                </ul>';

        $(".soft-man-con").html(con);
    });
}

function setDisableFunc(version, act, fs) {
    var fsArr = fs.split(',');
    if (act == 1) {
        var functions = $("#disable_function_val").val();
        for (var i = 0; i < fsArr.length; i++) {
            if (functions == fsArr[i]) {
                layer.msg(lan.soft.fun_msg, { icon: 5 });
                return;
            }
        }
        fs += ',' + functions;
        msg = 'Added successfully';
    } else {

        fs = '';
        for (var i = 0; i < fsArr.length; i++) {
            if (act == fsArr[i]) continue;
            fs += fsArr[i] + ','
        }
        msg = 'Successfully deleted';
        fs = fs.substr(0, fs.length - 1);
    }

    var data = {
        'version':version,
        'disable_functions':fs,
    };

    phpPost('set_disable_func', version,data,function(data){
        var rdata = $.parseJSON(data.data);
        showMsg(rdata.status ? msg : rdata.msg, function(){
            disableFunc(version);
        } ,{ icon: rdata.status ? 1 : 2 });
    });
}

function getPhpinfo(version) {
    var con = '<button class="btn btn-default btn-sm" onclick="getPHPInfo(\'' + version + '\')">View phpinfo()</button>';
    $(".soft-man-con").html(con);
}

function getPHPInfo_old(version) {
    phpPost('get_phpinfo', version, '', function(data){
        var rdata = data.data;
        layer.open({
            type: 1,
            title: "PHP-" + version + "-PHPINFO",
            area: ['90%', '90%'],
            closeBtn: 2,
            shadeClose: true,
            content: rdata
        });
    });
}

function getPHPInfo(version) {
    phpPostCallbak('get_php_info', version, {}, function(data){
        if (!data.status){
            layer.msg(rdata.msg, { icon: 2 });
            return;
        }

        layer.open({
            type: 1,
            title: "PHP-" + version + "-PHPINFO",
            area: ['70%', '90%'],
            closeBtn: 2,
            shadeClose: true,
            content: data.data.replace('a:link {color: #009; text-decoration: none; background-color: #fff;}', '').replace('a:link {color: #000099; text-decoration: none; background-color: #ffffff;}', '')
        });
    })
}


function phpLibConfig(version){

    phpPost('get_lib_conf', version, '', function(data){
        var rdata = $.parseJSON(data.data);

        if (!rdata.status){
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            return;
        }

        var libs = rdata.data;
        var body = '';
        var opt = '';

        for (var i = 0; i < libs.length; i++) {
            if (libs[i].versions.indexOf(version) == -1){
                continue;
            }

            if (libs[i]['task'] == '-1' && libs[i].phpversions.indexOf(version) != -1) {
                opt = '<a style="color:green;" href="javascript:messageBox();">Install</a>'
            } else if (libs[i]['task'] == '0' && libs[i].phpversions.indexOf(version) != -1) {
                opt = '<a style="color:#C0C0C0;" href="javascript:messageBox();">Waiting to install...</a>'
            } else if (libs[i].status) {
                opt = '<a style="color:red;" href="javascript:uninstallPHPLib(\'' + version + '\',\'' + libs[i].name + '\',\'' + libs[i].title + '\',' + '' + ');">Uninstall</a>'
            } else {
                opt = '<a class="btlink" href="javascript:installPHPLib(\'' + version + '\',\'' + libs[i].name + '\',\'' + libs[i].title + '\',' + '' + ');">Install</a>'
            }

            body += '<tr>' +
                '<td>' + libs[i].name + '</td>' +
                '<td>' + libs[i].type + '</td>' +
                '<td>' + libs[i].msg + '</td>' +
                '<td><span class="ico-' + (libs[i].status ? 'start' : 'stop') + ' glyphicon glyphicon-' + (libs[i].status ? 'ok' : 'remove') + '"></span></td>' +
                '<td style="text-align: right;">' + opt + '</td>' +
                '</tr>';
        }


        var con = '<div class="divtable" id="phpextdiv" style="margin-right:10px;height: 420px; overflow: auto; margin-right: 0px;">' +
            '<table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0">' +
            '<thead>' +
            '<tr>' +
            '<th>Name</th>' +
            '<th width="64">Type</th>' +
            '<th>Caption</th>' +
            '<th width="40">Status</th>' +
            '<th style="text-align: right;" width="50">Action</th>' +
            '</tr>' +
            '</thead>' +
            '<tbody>'  + body + '</tbody>' +
            '</table>' +
            '</div>' +
            '<ul class="help-info-text c7 pull-left">\
                <li>Please install extensions according to actual needs, do not install unnecessary PHP extensions, which will affect the efficiency of PHP execution and even cause exceptions</li>\
                <li>The Redis extension is only allowed to be used in one PHP version. To install other PHP versions, please reinstall Redis in [Software Management]</li>\
                <li>Script cache extensions such as opcache/xcache/apc, please install only one of them, otherwise it may cause your site program to be abnormal</li>\
                <li>ioncube should be installed before ZendGuardLoader/opcache, otherwise it may cause abnormality in your site program</li>\
            </ul>';
        $('.soft-man-con').html(con);
    });

}

function installPHPLib(version, name, title, pathinfo) {
    layer.confirm('Do you really want to install {1}?'.replace('{1}', name), { title:'Notification', icon: 3, closeBtn: 2, btn: ['Yes','No'] }, function() {
        name = name.toLowerCase();
        var data = "name=" + name + "&version=" + version + "&type=1";

        phpPost('install_lib', version, data, function(data){
            var rdata = $.parseJSON(data.data);
            // layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            showMsg(rdata.msg, function(){
                getTaskCount();
                phpLibConfig(version);
            },{ icon: rdata.status ? 1 : 2 });

        });
    });
}

function uninstallPHPLib(version, name, title, pathinfo) {
    layer.confirm('Do you really want to uninstall {1}?'.replace('{1}', name), { title:'Notification', icon: 3, closeBtn: 2, btn: ['Yes','No'] }, function() {
        name = name.toLowerCase();
        var data = 'name=' + name + '&version=' + version;
        phpPost('uninstall_lib', version, data, function(data){
            var rdata = $.parseJSON(data.data);
            // layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            showMsg(rdata.msg, function(){
                getTaskCount();
                phpLibConfig(version);
            },{ icon: rdata.status ? 1 : 2 },5000);

        });
    });
}

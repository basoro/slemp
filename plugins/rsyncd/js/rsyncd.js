function rsPost(method,args,callback, title){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(toArrayObject(args));
    } else {
        _args = JSON.stringify(args);
    }

    var _title = 'Retrieving...';
    if (typeof(title) != 'undefined'){
        _title = title;
    }

    var loadT = layer.msg(_title, { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'rsyncd', func:method, args:_args}, function(data) {
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

function createSendTask(name = ''){
    var args = {};
    args["name"] = name;
    rsPost('lsyncd_get', args, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        var data = rdata.data;
        console.log(data);

        var layerName = 'Create';
        if (name!=''){
            layerName = 'Edit';
        }

        var compress_true = "";
        var compress_false = "";
        if (data['rsync']['compress'] == 'true'){
            compress_true = "selected";
            compress_false = "";
        } else {
            compress_true = "";
            compress_false = "selected";
        }


        var delete_true = "";
        var delete_false = "";
        if (data['delete'] == 'false'){
            delete_true = "selected";
            delete_false = "";
        } else {
            delete_true = "";
            delete_false = "selected";
        }


        var realtime_true = "";
        var realtime_false = "";
        if (data['realtime'] == 'true'){
            realtime_true = "selected";
            realtime_false = "";
        } else {
            realtime_true = "";
            realtime_false = "selected";
        }


        var period_day = "";
        var period_minute_n = "";
        if (data['period'] == 'day'){
            period_day = "selected";
            period_minute_n = "";
        } else {
            period_day = "";
            period_minute_n = "selected";
        }


        var layerID = layer.open({
            type: 1,
            area: ['600px','500px'],
            title: layerName+" send task",
            closeBtn: 1,
            shift: 0,
            shadeClose: false,
            btn: ['Submit','Cancel'],
            content:"<form class='bt-form pd20' id='fromServerPath' accept-charset='utf-8'>\
                <div class='line'>\
                    <span class='tname'>Server IP</span>\
                    <div class='info-r c4'>\
                        <input class='bt-input-text' type='text' name='ip' placeholder='Please enter the receiving server IP' value='"+data["ip"]+"' style='width:310px' />\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Sync directory</span>\
                    <div class='info-r c4'>\
                        <input id='inputPath' class='bt-input-text mr5' type='text' name='path' value='"+data["path"]+"' placeholder='Please select a sync directory' style='width:310px' /><span class='glyphicon glyphicon-folder-open cursor' onclick='changePath(\"inputPath\")'></span>\
                        <span data-toggle='tooltip' data-placement='top' title='[Synchronization directory] If it does not end with /, it means that the data will be synchronized to the secondary directory. In general, the directory path should end with /' class='bt-ico-ask' style='cursor: pointer;'>?</span>\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Synchronously</span>\
                    <div class='info-r c4'>\
                        <select class='bt-input-text' name='delete' style='width:100px'>\
                            <option value='false' "+delete_true+">Incremental</option>\
                            <option value='true' "+delete_false+">Total</option>\
                        </select>\
                        <span data-toggle='tooltip' data-placement='top' title='[Synchronization method] Incremental: Synchronize when data is changed/increased, and only append and replace files' class='bt-ico-ask' style='cursor: pointer;'>?</span>\
                        <span style='margin-left: 20px;margin-right: 10px;'>Sync cycle</span>\
                        <select class='bt-input-text synchronization' name='realtime' style='width:100px'>\
                            <option value='true' "+realtime_true+">Real time</option>\
                            <option value='false' "+realtime_false+">Scheduled</option>\
                        </select>\
                    </div>\
                </div>\
                <div class='line' id='period' style='height:45px;display:none;'>\
                    <span class='tname'>Timing cycle</span>\
                    <div class='info-r c4'>\
                        <select class='bt-input-text pull-left mr20' name='period' style='width:100px;'>\
                            <option value='day' "+period_day+">Every day</option>\
                            <option value='minute-n' "+period_minute_n+">N minutes</option>\
                        </select>\
                        <div class='plan_hms pull-left mr20 bt-input-text hour'>\
                            <span><input class='bt-input-text' type='number' name='hour' value='"+data["hour"]+"' maxlength='2' max='23' min='0'></span>\
                            <span class='name'>Hour</span>\
                        </div>\
                        <div class='plan_hms pull-left mr20 bt-input-text minute'>\
                            <span><input class='bt-input-text' type='number' name='minute' value='"+data["minute"]+"' maxlength='2' max='59' min='0'></span>\
                            <span class='name'>Minutes</span>\
                        </div>\
                        <div class='plan_hms pull-left mr20 bt-input-text minute-n' style='display:none;'>\
                            <span><input class='bt-input-text' type='number' name='minute-n' value='"+data["minute-n"]+"' maxlength='2' max='59' min='0'></span>\
                            <span class='name'>Minutes</span>\
                        </div>\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Speed limit</span>\
                    <div class='info-r c4'>\
                        <input class='bt-input-text' type='number' name='bwlimit' min='0'  value='1024' style='width:100px' /> KB\
                        <span data-toggle='tooltip' data-placement='top' title='[Speed limit] Limit the speed of data synchronization tasks to prevent high bandwidth caused by synchronous data' class='bt-ico-ask' style='cursor: pointer;'>?</span>\
                        <span style='margin-left: 29px;margin-right: 10px;'>Delay</span><input class='bt-input-text' min='0' type='number' name='delay'  value='3' style='width:100px' /> Second\
                        <span data-toggle='tooltip' data-placement='top' title='[Delay] Only record out-of-sync during the delay time period, and synchronize the data at one time after reaching the period to save overhead' class='bt-ico-ask' style='cursor: pointer;'>?</span>\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Connection method</span>\
                    <div class='info-r c4'>\
                        <select class='bt-input-text' name='conn_type' style='width:100px'>\
                            <option value='key'>Key</option>\
                            <option value='user'>User</option>\
                        </select>\
                        <span style='margin-left: 45px;margin-right: 10px;'>Compressed transmission</span>\
                        <select class='bt-input-text' name='compress' style='width:100px'>\
                            <option value='true' "+compress_true+">Compressed</option>\
                            <option value='false' "+compress_false+">Uncompressed</option>\
                        </select>\
                        <span data-toggle='tooltip' data-placement='top' title='[Compressed Transmission] Enabled to reduce bandwidth overhead, but will increase CPU overhead, if the bandwidth is sufficient, it is recommended to turn off this option' class='bt-ico-ask' style='cursor: pointer;'>?</span>\
                    </div>\
                </div>\
                <div class='line conn-key'>\
                    <span class='tname'>Receive key</span>\
                    <div class='info-r c4'>\
                        <textarea id='mainDomain' class='bt-input-text' name='secret_key' style='width:310px;height:75px;line-height:22px' placeholder='This key is the key of receiving configuration [receiving account number]'>"+data['secret_key']+"</textarea>\
                    </div>\
                </div>\
                <div class='line conn-user'>\
                    <span class='tname'>Username</span>\
                    <div class='info-r c4'>\
                        <input class='bt-input-text' type='text' name='u_user' min='0'  value='"+data["name"]+"' style='width:310px' />\
                    </div>\
                </div>\
                <div class='line conn-user'>\
                    <span class='tname'>Password</span>\
                    <div class='info-r c4'>\
                        <input class='bt-input-text' type='text' name='u_pass' min='0'  value='"+data["password"]+"' style='width:310px' />\
                    </div>\
                </div>\
                <div class='line conn-user'>\
                    <span class='tname'>Port</span>\
                    <div class='info-r c4'>\
                        <input class='bt-input-text' type='number' name='u_port' min='0'  value='"+data["rsync"]["port"]+"' style='width:310px' />\
                    </div>\
                </div>\
                <ul class=\"help-info-text c7\">\
                </ul>\
              </form>",
            success:function(){
                $('[data-toggle="tooltip"]').tooltip();

                $(".conn-user").hide();
                $("select[name='conn_type']").change(function(){
                    if($(this).val() == 'key'){
                        $(".conn-user").hide();
                        $(".conn-key").show();
                    }else{
                        $(".conn-user").show();
                        $(".conn-key").hide();
                    }
                });


                var selVal = $('.synchronization option:selected').val();
                if (selVal == "false"){
                    $('#period').show();
                }else{
                    $('#period').hide();
                    $('.hour input,.minute input').val('0');
                    $('.minute-n input').val('1');
                }
                $('.synchronization').change(function(event) {
                    var selVal = $('.synchronization option:selected').val();
                    if (selVal == "false"){
                        $('#period').show();
                    }else{
                        $('#period').hide();
                        $('.hour input,.minute input').val('0');
                        $('.minute-n input').val('1');
                    }
                });

                $("select[name='delete']").change(function(){
                    if($(this).val() == 'true'){
                        var mpath = $('input[name="path"]').val();
                        var msg = '<div><span style="color:orangered;">Warning: You have selected full synchronization, which will make the local synchronization consistent with the files in the specified directory of the target machine，'
                            +'<br />Please confirm whether the directory setting is correct. Once the setting is wrong, the directory file of the target machine may be deleted!</span>'
                            +'<br /><br /> <span style="color:red;">Note: The sync program will copy the local directory：'
                            +mpath+'All data in the target server will be synchronized to the target server. If there are other files in the target server\'s synchronization directory, they will be deleted!</span> <br /><br /> Know the risks, please press OK to continue</div>';

                        layer.confirm(msg,{title:'Data Security Risk Warning',icon:2,closeBtn: 1,shift: 5,
                        btn2:function(){
                            setTimeout(function(){$($("select[name='delete']").children("option")[0]).prop('selected',true);},100);
                        }
                        });
                    }
                });


                var selVal = $('#period select option:selected').val();
                if (selVal == 'day'){
                    $('.hour,.minute').show();
                    if ($('.hour input').val() == ''){
                        $('.hour input,.minute input').val('0');
                    }
                    $('.minute-n').hide();
                }else{
                    $('.hour,.minute').hide();
                    $('.minute-n').show();
                    if ($('.minute-n input').val() == ''){
                        $('.minute-n input').val('1');
                    }
                }
                $('#period').change(function(event) {
                    var selVal = $('#period select option:selected').val();
                    if (selVal == 'day'){
                        $('.hour,.minute').show();
                        if ($('.hour input').val() == ''){
                            $('.hour input,.minute input').val('0');
                        }
                        $('.minute-n').hide();
                    }else{
                        $('.hour,.minute').hide();
                        $('.minute-n').show();
                        if ($('.minute-n input').val() == ''){
                            $('.minute-n input').val('1');
                        }
                    }
                });
            },
            yes:function(index){
                var args = {};
                var conn_type = $("select[name='conn_type']").val();

                if(conn_type == 'key'){
                    if ( $('textarea[name="secret_key"]').val() != ''){
                        args['secret_key'] = $('textarea[name="secret_key"]').val();
                    } else {
                        layer.msg('Please enter the receive key!');
                        return false;
                    }
                } else {
                    args['sname'] = $("input[name='u_user']").val();
                    args['password'] = $("input[name='u_pass']").val();
                    var port = Number($("input[name='u_port']").val());
                    args['port'] = port;
                    if (!args['sname'] || !args['password'] || !args['port']){
                        layer.msg('Please enter account, password, port information');
                        return false;
                    }
                }

                if ($('input[name="ip"]').val() == ''){
                    layer.msg('Please enter the server IP address!');
                    return false;
                }

                args['sname'] = $("input[name='u_user']").val();
                args['password'] = $("input[name='u_pass']").val();
                var port = Number($("input[name='u_port']").val());
                args['port'] = port;


                args['ip'] = $('input[name="ip"]').val();
                args['path'] = $('input[name="path"]').val();
                args['delete'] = $('select[name="delete"]').val();
                args['realtime'] = $('select[name="realtime"]').val();
                args['delay'] = $('input[name="delay"]').val();

                args['bwlimit'] = $('input[name="bwlimit"]').val();
                args['conn_type'] = $('select[name="conn_type"]').val();
                args['compress'] = $('select[name="compress"]').val();

                args['period'] = $('select[name="period"]').val();
                args['hour'] = $('input[name="hour"]').val();
                args['minute'] = $('input[name="minute"]').val();
                args['minute-n'] = $('input[name="minute-n"]').val();

                rsPost('lsyncd_add', args, function(rdata){
                    var rdata = $.parseJSON(rdata.data);
                    layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});

                    if (rdata.status){
                         setTimeout(function(){
                            layer.close(index);
                            lsyncdSend();
                         },2000);
                        return;
                    }
                });
                return true;
            }
        });
    });
}

function lsyncdDelete(name){
    safeMessage('Delete ['+name+']', 'Do you really want to delete ['+name+']？', function(){
        var args = {};
        args['name'] = name;
        rsPost('lsyncd_delete', args, function(rdata){
            var rdata = $.parseJSON(rdata.data);
            layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
            setTimeout(function(){lsyncdSend();},2000);
        });
    });
}


function lsyncdRun(name){
    var args = {};
    args["name"] = name;
    rsPost('lsyncd_run', args, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
    });
}

function lsyncdLog(name){
    var args = {};
    args["name"] = name;
    pluginStandAloneLogs("rsyncd", '', "lsyncd_log", JSON.stringify(args));
}


function lsyncdExclude(name){
    layer.open({
        type:1,
        title:'Filter',
        area: '400px',
        shadeClose:false,
        closeBtn:2,
        content:'<div class="lsyncd_exclude">\
                <div style="overflow:hidden;">\
                    <fieldset>\
                        <legend>Excluded files and directories</legend>\
                        <input type="text" class="bt-input-text mr5" data-type="exclude" title="For example：/home/www/" placeholder="For example：*.log" style="width:305px;">\
                        <button data-type="exclude" class=" addList btn btn-default btn-sm">Add</button>\
                        <div class="table-overflow">\
                            <table class="table table-hover BlockList"><tbody></tbody></table>\
                        </div>\
                    </fieldset>\
                </div>\
                <div>\
                    <ul class="help-info-text c7" style="list-style-type:decimal;">\
                        <li>Excluded files and directories refer to directories or files that do not need to be synchronized in the current directory</li>\
                        <li>If the rule starts with a slash <code>/</code>, it will match all from the beginning</li>\
                        <li>If the rule ends with <code>/</code>, it matches the end of the monitoring path</li>\
                        <li><code>?</code> matches any character but does not include <code>/</code></li>\
                        <li><code>*</code> matches 0 or more characters, but does not include <code>/</code></li>\
                        <li><code>**</code> matches 0 or more characters, can be <code>/</code></li>\
                    </ul>\
                </div>\
            </div>'
    });

    function getIncludeExclude(mName){
        loadT = layer.msg('Fetching data...',{icon:16,time:0,shade: [0.3, '#000']});
        rsPost('lsyncd_get_exclude',{"name":mName}, function(rdata) {
            layer.close(loadT);

            var rdata = $.parseJSON(rdata.data);
            var res = rdata.data;

            var list=''
            for (var i = 0; i < res.length; i++) {
                list += '<tr><td>'+ res[i] +'</td><td><a href="javascript:;" data-type='+ mName +' class="delList">Delete</a></td></tr>';
            }
            $('.lsyncd_exclude .BlockList tbody').empty().append(list);
        });
    }
    getIncludeExclude(name);


    function addArgs(name,exclude){
        loadT = layer.msg('Adding...',{icon:16,time:0,shade: [0.3, '#000']});
        rsPost('lsyncd_add_exclude', {name:name,exclude:exclude}, function(res){
            layer.close(loadT);

            console.log('addArgs:',res);

            if (res.status){
                getIncludeExclude(name);
                $('.lsyncd_exclude input').val('');
                layer.msg(res.msg);
            }else{
                layer.msg(res.msg);
            }
        });
    }
    $('.addList').click(function(event) {
        var val = $(this).prev().val();
        if(val == ''){
            layer.msg('The current input content is empty, please enter');
            return false;
        }
        addArgs(name,val);
    });
    $('.lsyncd_exclude input').keyup(function(event){
        if (event.which == 13){
            var val = $(this).val();
            if(val == ''){
                layer.msg('The current input content is empty, please enter');
                return false;
            }
            addArgs(name,val);
        }
    });


    $('.lsyncd_exclude').on('click', '.delList', function(event) {
        loadT = layer.msg('Deleting...',{icon:16,time:0,shade: [0.3, '#000']});
        var val = $(this).parent().prev().text();
        rsPost('lsyncd_remove_exclude',{"name":name,exclude:val}, function(rdata) {
            layer.close(loadT);

            console.log(rdata)
            var rdata = $.parseJSON(rdata.data);
            var res = rdata.data;

            var list=''
            for (var i = 0; i < res.length; i++) {
                list += '<tr><td>'+ res[i] +'</td><td><a href="javascript:;" data-type='+ name +' class="delList">Delete</a></td></tr>';
            }
            $('.lsyncd_exclude .BlockList tbody').empty().append(list);
        });
    });
}

function lsyncdConfLog(){
    pluginStandAloneLogs("rsyncd","","lsyncd_conf_log");;
}

function lsyncdSend(){
    rsPost('lsyncd_list', '', function(data){
        var rdata = $.parseJSON(data.data);
        console.log(rdata);
        if (!rdata.status){
            layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
            return;
        }
        var list = rdata.data.list;
        var con = '';

        con += '<div style="padding-top:1px;">\
                <button class="btn btn-success btn-sm" onclick="createSendTask();">Create send task</button>\
                <button class="btn btn-success btn-sm" onclick="lsyncdConfLog();">Log</button>\
            </div>';

        con += '<div class="divtable" style="margin-top:5px;"><table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0">';
        con += '<thead><tr>';
        con += '<th>Name (identification)</th>';
        con += '<th>Source directory</th>';
        con += '<th>Sync to</th>';
        con += '<th>Model</th>';
        con += '<th>Cycle</th>';
        con += '<th>Action</th>';
        con += '</tr></thead>';

        con += '<tbody>';



        for (var i = 0; i < list.length; i++) {
            var mode = 'Incremental';
            if (list[i]['delete'] == 'true'){
                mode = 'Total';
            } else {
                mode = 'Incremental';
            }

            var period = "Real time";
            if (list[i]['realtime'] == 'true'){
                period = 'Real time';
            } else {
                period = 'Scheduled';
            }

            con += '<tr>'+
                '<td>' + list[i]['name']+'</td>' +
                '<td><a class="btlink overflow_hide" style="width:40px;" onclick="openPath(\''+list[i]['path']+'\')">' + list[i]['path']+'</a></td>' +
                '<td>' + list[i]['ip']+":"+list[i]['name']+'</td>' +
                '<td>' + mode+'</td>' +
                '<td>' + period +'</td>' +
                '<td>\
                    <a class="btlink" onclick="lsyncdRun(\''+list[i]['name']+'\')">Synchronize</a>\
                    | <a class="btlink" onclick="lsyncdLog(\''+list[i]['name']+'\')">Log</a>\
                    | <a class="btlink" onclick="lsyncdExclude(\''+list[i]['name']+'\')">Filter</a>\
                    | <a class="btlink" onclick="createSendTask(\''+list[i]['name']+'\')">Edit</a>\
                    | <a class="btlink" onclick="lsyncdDelete(\''+list[i]['name']+'\')">Delete</a>\
                </td>\
                </tr>';
        }

        con += '</tbody>';
        con += '</table></div>';

        $(".soft-man-con").html(con);
    });
}


function rsyncdConf(){
    rsPost('conf', {}, function(rdata){
        rpath = rdata['data'];
        if (rdata['status']){
            onlineEditFile(0, rpath);
        } else {
            layer.msg(rdata.msg,{icon:1,time:2000,shade: [0.3, '#000']});
        }
    });
}

function rsyncdLog(){
    pluginStandAloneLogs("rsyncd","","run_log");
}


function rsyncdReceive(){
	rsPost('rec_list', '', function(data){
		var rdata = $.parseJSON(data.data);
		if (!rdata.status){
			layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
			return;
		}
		// console.log(rdata);
		var list = rdata.data;
		var con = '';

        con += '<div style="padding-top:1px;">\
                <button class="btn btn-success btn-sm" onclick="rsyncdConf();">Config</button>\
                <button class="btn btn-success btn-sm" onclick="rsyncdLog();">Log</button>\
            </div>';

        con += '<div class="divtable" style="margin-top:5px;"><table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0">';
        con += '<thead><tr>';
        con += '<th>Service Name</th>';
        con += '<th>Path</th>';
        con += '<th>Description</th>';
        con += '<th>Action (<a class="btlink" onclick="addReceive()">Add</a>)</th>';
        con += '</tr></thead>';

        con += '<tbody>';

        //<a class="btlink" onclick="modReceive(\''+list[i]['name']+'\')">Edit</a>
        for (var i = 0; i < list.length; i++) {
            con += '<tr>'+
                '<td>' + list[i]['name']+'</td>' +
                '<td><a class="btlink overflow_hide" onclick="openPath(\''+list[i]['path']+'\')">' + list[i]['path']+'</a></td>' +
                '<td>' + list[i]['comment']+'</td>' +
                '<td>\
                    <a class="btlink" onclick="cmdRecCmd(\''+list[i]['name']+'\')">Order</a>\
                	| <a class="btlink" onclick="cmdRecSecretKey(\''+list[i]['name']+'\')">Key</a>\
                    | <a class="btlink" onclick="addReceive(\''+list[i]['name']+'\')">Edit</a>\
                	| <a class="btlink" onclick="delReceive(\''+list[i]['name']+'\')">Delete</a></td>\
                </tr>';
        }

        con += '</tbody>';
        con += '</table></div>';

        $(".soft-man-con").html(con);
	});
}


function addReceive(name = ""){
    rsPost('get_rec',{"name":name},function(rdata) {
        var rdata = $.parseJSON(rdata.data);
        var data = rdata.data;

        var readonly = "";
        if (name !=""){
            readonly = 'readonly="readonly"'
        }

        var loadOpen = layer.open({
            type: 1,
            title: 'Create receive',
            area: '400px',
            btn:['Submit','Cancel'],
            content:"<div class='bt-form pd20 c6'>\
                <div class='line'>\
                    <span class='tname'>Item name</span>\
                    <div class='info-r c4'>\
                        <input id='name' value='"+data["name"]+"' class='bt-input-text' type='text' name='name' placeholder='Item name' style='width:200px' "+readonly+"/>\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Key</span>\
                    <div class='info-r c4'>\
                        <input id='MyPassword' value='"+data["pwd"]+"' class='bt-input-text' type='text' name='pwd' placeholder='Key' style='width:200px'/>\
                        <span title='Random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span>\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Sync to</span>\
                    <div class='info-r c4'>\
                        <input id='inputPath' value='"+data["path"]+"' class='bt-input-text' type='text' name='path' placeholder='/' style='width:200px'/>\
                        <span class='glyphicon glyphicon-folder-open cursor' onclick=\"changePath('inputPath')\"></span>\
                    </div>\
                </div>\
                <div class='line'>\
                    <span class='tname'>Description</span>\
                    <div class='info-r c4'>\
                        <input id='ps' class='bt-input-text' type='text' name='ps' value='"+data["comment"]+"' placeholder='Description' style='width:200px'/>\
                    </div>\
                </div>\
            </div>",
            success:function(layero, index){},
            yes:function(){
                var args = {};
                args['name'] = $('#name').val();
                args['pwd'] = $('#MyPassword').val();
                args['path'] = $('#inputPath').val();
                args['ps'] = $('#ps').val();
                var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });
                rsPost('add_rec', args, function(data){
                    var rdata = $.parseJSON(data.data);
                    layer.close(loadOpen);
                    layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
                    setTimeout(function(){rsyncdReceive();},2000);
                });
            }
        });
    })
}


function delReceive(name){
	safeMessage('Delete ['+name+']', 'Do you really want to delete ['+name+']?', function(){
		var _data = {};
		_data['name'] = name;
		rsPost('del_rec', _data, function(data){
            var rdata = $.parseJSON(data.data);
            layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
            setTimeout(function(){rsyncdReceive();},2000);
        });
	});
}

function cmdRecSecretKey(name){
	var _data = {};
	_data['name'] = name;
	rsPost('cmd_rec_secret_key', _data, function(data){
        var rdata = $.parseJSON(data.data);
	    layer.open({
	        type: 1,
	        title: 'Receive key',
	        area: '400px',
	        content:"<div class='bt-form pd20 pb70 c6'><textarea class='form-control' rows='6' readonly='readonly'>"+rdata.data+"</textarea></div>"
    	});
    });
}

function cmdRecCmd(name){
    var _data = {};
    _data['name'] = name;
    rsPost('cmd_rec_cmd', _data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.open({
            type: 1,
            title: 'Receive command example',
            area: '400px',
            content:"<div class='bt-form pd20 pb70 c6'>"+rdata.data+"</div>"
        });
    });
}


function rsRead(){
	var readme = '<ul class="help-info-text c7">';
    readme += '<li>To synchronize data from other servers to the local server, please "create a receive task" in the receive configuration</li>';
    readme += '<li>If the firewall is enabled, port 873 needs to be released</li>';
    readme += '</ul>';

    $('.soft-man-con').html(readme);
}

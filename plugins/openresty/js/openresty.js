function orPost(method, args, callback){
    var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'openresty', func:method, args:JSON.stringify(args)}, function(data) {
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

function orPluginService(_name, version){
    var data = {name:_name, func:'status'}
    if ( typeof(version) != 'undefined' ){
        data['version'] = version;
    } else {
        version = '';
    }

    orPost('status', data, function(data){
        if (data.data == 'start'){
            orPluginSetService(_name, true, version);
        } else {
            orPluginSetService(_name, false, version);
        }
    });
}

function orPluginSetService(_name ,status, version){
    var serviceCon ='<p class="status">Current status：<span>'+(status ? 'start' : 'stop' )+
        '</span><span style="color: '+
        (status?'#20a53a;':'red;')+
        ' margin-left: 3px;" class="glyphicon ' + (status?'glyphicon glyphicon-play':'glyphicon-pause')+'"></span></p><div class="sfm-opt">\
            <button class="btn btn-default btn-sm" onclick="orPluginOpService(\''+_name+'\',\''+(status?'stop':'start')+'\',\''+version+'\')">'+(status?'Stop':'Start')+'</button>\
            <button class="btn btn-default btn-sm" onclick="orPluginOpService(\''+_name+'\',\'restart\',\''+version+'\',\'yes\')">Restart</button>\
            <button class="btn btn-default btn-sm" onclick="orPluginOpService(\''+_name+'\',\'reload\',\''+version+'\')">Reload</button>\
        </div>';
    $(".soft-man-con").html(serviceCon);
}


function orPluginOpService(a, b, v,request_callback) {

    var c = "name=" + a + "&func=" + b;
    if(v != ''){
        c = c + '&version='+v;
    }

    var d = "";

    switch(b) {
        case "stop":d = 'stop';break;
        case "start":d = 'start';break;
        case "restart":d = 'restart';break;
        case "reload":d = 'reload';break;
    }
    layer.confirm( msgTpl('Do you really want {1}{2}{3} service？', [d,a,v]), {icon:3,closeBtn: 2}, function() {
        orPost('get_os',{},function(data){
            var rdata = $.parseJSON(data.data);
            if (!rdata['auth']){
                layer.prompt({title: 'Insufficient permissions were detected, a password is required!', formType: 1},function(pwd, index){

                    layer.close(index);
                    var data = {'pwd':pwd};
                    c += '&args='+JSON.stringify(data);
                    orPluginOpServiceOp(a,b,c,d,a,v,request_callback);
                });
            } else {
                orPluginOpServiceOp(a,b,c,d,a,v,request_callback);

            }
        });
    })
}

function orPluginOpServiceOp(a,b,c,d,a,v,request_callback){

    var request_path = "/plugins/run";
    if (request_callback == 'yes'){
        request_path = "/plugins/callback";
    }

    var e = layer.msg(msgTpl('Serving {1}{2}{3}, please wait...',[d,a,v]), {icon: 16,time: 0});
    $.post(request_path, c, function(g) {
        layer.close(e);

        var f = g.data == 'ok' ? msgTpl('{1} {2} service has been {3}',[a,v,d]) : msgTpl('{1}{2} failed to serve {3}!',[a,v,d]);
        layer.msg(f, {icon: g.data == 'ok' ? 1 : 2});

        if( b != "reload" && g.data == 'ok' ) {
            if ( b == 'start' ) {
                orPluginSetService(a, true, v);
            } else if ( b == 'stop' ){
                orPluginSetService(a, false, v);
            }
        }

        if( g.status && g.data != 'ok' ) {
            layer.msg(g.data, {icon: 2,time: 10000,shade: 0.3});
        }

    },'json').error(function() {
        layer.close(e);
        layer.msg('Abnormal operation!', {icon: 2});
    });
}

function getOpStatus() {
    var loadT = layer.msg('Processing, please wait...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'openresty', func:'run_info'}, function(data) {
        layer.close(loadT);
        if (!data.status){
            showMsg(data.msg, function(){}, null,3000);
            return;
        }
        try {
            var rdata = $.parseJSON(data.data);
            var con = "<div><table class='table table-hover table-bordered'>\
                            <tr><th>Active connections</th><td>" + rdata.active + "</td></tr>\
                            <tr><th>Accepts</th><td>" + rdata.accepts + "</td></tr>\
                            <tr><th>Handled</th><td>" + rdata.handled + "</td></tr>\
                            <tr><th>Requests</th><td>" + rdata.requests + "</td></tr>\
                            <tr><th>Reading</th><td>" + rdata.Reading + "</td></tr>\
                            <tr><th>Writing</th><td>" + rdata.Writing + "</td></tr>\
                            <tr><th>Waiting</th><td>" + rdata.Waiting + "</td></tr>\
                         </table></div>";
            $(".soft-man-con").html(con);
        }catch(err){
             showMsg(data.data, function(){}, null,3000);
        }
    },'json');
}


function setOpCfg(){
    orPost('get_cfg', {}, function(data){
        var rdata = $.parseJSON(data.data);
        var rdata = rdata.data;
        // console.log(rdata);

        var mlist = '';
        for (var i = 0; i < rdata.length; i++) {
            var w = '70'
            var ibody = '<input style="width: ' + w + 'px;" class="bt-input-text mr5" name="' + rdata[i].name + '" value="' + rdata[i].value + '" type="text" >';
            switch (rdata[i].type) {
                case 0:
                    var selected_1 = (rdata[i].value == 1) ? 'selected' : '';
                    var selected_0 = (rdata[i].value == 0) ? 'selected' : '';
                    ibody = '<select class="bt-input-text mr5" name="' + rdata[i].name + '" style="width: ' + w + 'px;">\
                        <option value="1" ' + selected_1 + '>start</option>\
                        <option value="0" ' + selected_0 + '>stop</option>\
                    </select>';
                    break;
                case 1:
                    var selected_1 = (rdata[i].value == 'on') ? 'selected' : '';
                    var selected_0 = (rdata[i].value == 'off') ? 'selected' : '';
                    ibody = '<select class="bt-input-text mr5" name="' + rdata[i].name + '" style="width: ' + w + 'px;">\
                        <option value="on" ' + selected_1 + '>start</option>\
                        <option value="off" ' + selected_0 + '>stop</option>\
                    </select>';
                    break;
            }
            mlist += '<p style="margin-top:15px;"><span>' + rdata[i].name + '</span>' + ibody + "<b class='unit c9'>"+rdata[i].unit+"</b>" +', <font class="c9">' + rdata[i].ps + '</font></p>';
        }
        var con = '<style>.conf_p p{margin-bottom: 2px}</style><div class="conf_p" style="margin-bottom:0">\
                        ' + mlist + '\
                        <div style="margin-top:10px; padding-right:15px" class="text-right">\
                            <button class="btn btn-success btn-sm mr5" onclick="setOpCfg()">Refresh</button>\
                            <button class="btn btn-success btn-sm" onclick="submitConf()">Save</button>\
                        </div>\
                    </div>'
        $(".soft-man-con").html(con);
    });
}

function submitConf() {
    var data = {
        worker_processes: $("input[name='worker_processes']").val(),
        worker_connections: $("input[name='worker_connections']").val(),
        keepalive_timeout: $("input[name='keepalive_timeout']").val(),
        gzip: $("select[name='gzip']").val() || 'on',
        gzip_min_length: $("input[name='gzip_min_length']").val(),
        gzip_comp_level: $("input[name='gzip_comp_level']").val(),
        client_max_body_size: $("input[name='client_max_body_size']").val(),
        server_names_hash_bucket_size: $("input[name='server_names_hash_bucket_size']").val(),
        client_header_buffer_size: $("input[name='client_header_buffer_size']").val(),
    };

    // console.log(data);
    orPost('set_cfg', data, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        // console.log(rdata);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

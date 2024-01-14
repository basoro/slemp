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
    var serviceCon ='<p class="status">Current state：<span>'+(status ? 'start' : 'stop' )+
        '</span><span style="color: '+
        (status?'#20a53a;':'red;')+
        ' margin-left: 3px;" class="glyphicon ' + (status?'glyphicon glyphicon-play':'glyphicon-pause')+'"></span></p><div class="sfm-opt">\
            <button class="btn btn-default btn-sm" onclick="orPluginOpService(\''+_name+'\',\''+(status?'stop':'start')+'\',\''+version+'\')">'+(status?'stop':'start')+'</button>\
            <button class="btn btn-default btn-sm" onclick="orPluginOpService(\''+_name+'\',\'restart\',\''+version+'\',\'yes\')">restart</button>\
            <button class="btn btn-default btn-sm" onclick="orPluginOpService(\''+_name+'\',\'reload\',\''+version+'\')">reload</button>\
        </div>';
    $(".soft-man-con").html(serviceCon);
}


function orPluginOpService(a, b, v, request_callback) {

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
    layer.confirm( msgTpl('Do you really want {1}{2}{3} services？', [d,a,v]), {title:'Notification',icon:3,closeBtn: 2,btn:['Yes','No']}, function() {
        orPost('get_os',{},function(data){
            var rdata = $.parseJSON(data.data);
            if (!rdata['auth']){
                layer.prompt({title: 'Insufficient permission is checked, a password is required!', formType: 1},function(pwd, index){

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

    var e = layer.msg(msgTpl('Serving on {1}{2}{3}, please wait...',[d,a,v]), {icon: 16,time: 0});
    $.post(request_path, c, function(g) {
        layer.close(e);

        var f = g.data == 'ok' ? msgTpl('{1}{2} serviced {3}',[a,v,d]) : msgTpl('{1}{2} Service {3} failed!',[a,v,d]);
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

function getOpenrestyStatus() {
    $.post('/plugins/run', {name:'openresty', func:'run_info'}, function(data) {
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

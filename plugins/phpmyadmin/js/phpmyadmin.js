function str2Obj(str){
    var data = {};
    kv = str.split('&');
    for(i in kv){
        v = kv[i].split('=');
        data[v[0]] = v[1];
    }
    return data;
}

function pmaPost(method,args,callback){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(str2Obj(args));
    } else {
        _args = JSON.stringify(args);
    }

    var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'phpmyadmin', func:method, args:_args}, function(data) {
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


function pmaAsyncPost(method,args){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(str2Obj(args));
    } else {
        _args = JSON.stringify(args);
    }
    return syncPost('/plugins/run', {name:'phpmyadmin', func:method, args:_args});
}

function homePage(){
    pmaPost('get_home_page', '', function(data){
        var rdata = $.parseJSON(data.data);
        if (!rdata.status){
            layer.msg(rdata.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }
        var con = '<button class="btn btn-default btn-sm" onclick="window.open(\'' + rdata.data + '\')">Homepage</button>';
        $(".soft-man-con").html(con);
    });
}

function phpVer(version) {

    var _version = pmaAsyncPost('get_set_php_ver','')
    if (_version['data'] != ''){
        version = _version['data'];
    }

    $.post('/site/get_php_version', function(rdata) {
        // console.log(rdata);
        var body = "<div class='ver line'><span class='tname'>PHP version</span><select id='phpver' class='bt-input-text mr20' name='phpVersion' style='width:110px'>";
        var optionSelect = '';
        for (var i = 0; i < rdata.length; i++) {
            optionSelect = rdata[i].version == version ? 'selected' : '';
            body += "<option value='" + rdata[i].version + "' " + optionSelect + ">" + rdata[i].name + "</option>"
        }
        body += '</select><button class="btn btn-success btn-sm" onclick="phpVerChange(\'phpversion\',\'get\')">Save</button></div>';
        $(".soft-man-con").html(body);
    },'json');
}

function phpVerChange(type, msg) {
    var phpver = $("#phpver").val();
    pmaPost('set_php_ver', 'phpver='+phpver, function(data){
        if ( data.data == 'ok' ){
            layer.msg('Successfully set!',{icon:1,time:2000,shade: [0.3, '#000']});
        } else {
            layer.msg('Setup failed!',{icon:2,time:2000,shade: [0.3, '#000']});
        }
    });
}


function safeConf() {
    pmaPost('get_pma_option', {}, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        if (!rdata.status){
            layer.msg(rdata.msg,{icon:2,time:2000,shade: [0.3, '#000']});
            return;
        }

        var cfg = rdata.data;
        var con = '<div class="ver line">\
                    <span class="tname">Access port</span>\
                    <input style="width:110px" class="bt-input-text phpmyadmindk mr20" name="Name" id="pmport" value="' + cfg['port'] + '" placeholder="Phpmyadmin access port" maxlength="5" type="number">\
                    <button class="btn btn-success btn-sm" onclick="setPamPort()">Save</button>\
                </div>\
                <div class="ver line">\
                    <span class="tname">Access switch</span>\
                    <select id="access_choose" class="bt-input-text mr20" name="choose" style="width:110px">\
                        <option value="mariadb" '+(cfg['choose']=="mariadb"?"selected='selected'":"")+'>MariaDB</option>\
                        <option value="mysql" '+ (cfg['choose']=="mysql"?"selected='selected'":"")+'>MySQL</option>\
                    </select>\
                    <button class="btn btn-success btn-sm" onclick="setPmaChoose()">Save</button>\
                </div>\
                <div class="ver line">\
                    <span class="tname">Username</span>\
                    <input style="width:110px" class="bt-input-text mr20" name="username" id="pmport" value="' + cfg['username'] + '" placeholder="Authentication username" type="text">\
                    <button class="btn btn-success btn-sm" onclick="setPmaUsername()">Save</button>\
                </div>\
                <div class="ver line">\
                    <span class="tname">Password</span>\
                    <input style="width:110px" class="bt-input-text mr20" name="password" id="pmport" value="' + cfg['password'] + '" placeholder="Password" type="text">\
                    <button class="btn btn-success btn-sm" onclick="setPmaPassword()">Save</button>\
                </div>\
                <hr/>\
                <div class="ver line">\
                    <span class="tname">Path name</span>\
                    <input style="width:180px" class="bt-input-text mr20" name="path" id="pmport" value="' + cfg['path'] + '" placeholder="" type="text">\
                    <button class="btn btn-success btn-sm" onclick="setPmaPath()">Save</button>\
                </div>';
        $(".soft-man-con").html(con);
    });
}


function setPmaChoose(){
    var choose = $("#access_choose").val();
    pmaPost('set_pma_choose',{'choose':choose}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function setPmaUsername(){
    var username = $("input[name=username]").val();
    pmaPost('set_pma_username',{'username':username}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function setPmaPassword(){
    var password = $("input[name=password]").val();
    pmaPost('set_pma_password',{'password':password}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function setPmaPath(){
    var path = $("input[name=path]").val();
    pmaPost('set_pma_path',{'path':path}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function setPamPort() {
    var pmport = $("#pmport").val();
    if (pmport < 80 || pmport > 65535) {
        layer.msg('Invalid port range!', { icon: 2 });
        return;
    }
    var data = 'port=' + pmport;

    pmaPost('set_pma_port',data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}


function str2Obj(str){
    var data = {};
    kv = str.split('&');
    for(i in kv){
        v = kv[i].split('=');
        data[v[0]] = v[1];
    }
    return data;
}


function pm2Post(method,args,callback){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(str2Obj(args));
    } else {
        _args = JSON.stringify(args);
    }

    var loadT = layer.msg('Getting...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'pm2', func:method, args:_args}, function(data) {
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



function pm2List() {
	var con = '<div class="divtable" style="width:620px;">\
				<input class="bt-input-text mr5" id="mmpath" name="path" type="text" value="" style="width:260px" placeholder="The root directory of the project">\
				<span onclick="changePath(\'mmpath\')" class="glyphicon glyphicon-folder-open cursor mr20"></span>\
				<input class="bt-input-text mr5" name="run" type="text" value="" style="width:150px" placeholder="Startup file name">\
				<input class="bt-input-text mr5" name="pname" type="text" value="" style="width:100px" placeholder="Project name">\
				<button class="btn btn-default btn-sm va0" onclick="addNode();">Add</button>\
				<table class="table table-hover" style="margin-top: 10px; max-height: 380px; overflow: auto;">\
					<thead>\
						<tr><th>Name</th>\
						<th>Model</th>\
						<th>Port</th>\
						<th>Status</th>\
						<th>Reboot</th>\
						<th>Time</th>\
						<th>CPU</th>\
						<th>RAM</th>\
						<th>Content</th>\
						<th style="text-align: right;" width="150">Action</th></tr>\
					</thead>\
					<tbody id="pmlist"></tbody>\
				</table>\
		</div>';

	$(".soft-man-con").html(con);


	pm2Post('list','', function(data){
		var rdata = $.parseJSON(data.data);
		console.log(rdata);
		if (!rdata['status']){
            layer.msg(rdata['msg'],{icon:2,time:2000,shade: [0.3, '#000']});
            return;
        }

        var tbody = '';
        var tmp = rdata['data'];
        for(var i=0;i<tmp.length;i++){
            if(tmp[i].status != 'online'){
                var opt = '<a href="javascript:nodeStart(\''+tmp[i].name+'\')" class="btlink">Start</a> | ';
            }else{
                var opt = '<a href="javascript:nodeStop(\''+tmp[i].name+'\')" class="btlink">Stop</a> | ';
            }
            tmp[i].path = tmp[i].path.replace('//','');

            var status = '<span style="color:rgb(92, 184, 92)" class="glyphicon glyphicon-play"></span>';
            if(tmp[i].status != 'online'){
                status = '<span style="color:rgb(255, 0, 0);" class="glyphicon glyphicon-pause"></span>';
            }

            tbody += '<tr>\
                        <td>'+tmp[i].name+'</td>\
                        <td>'+tmp[i].mode+'</td>\
                        <td>'+tmp[i].port+'</td>\
                        <td>'+status+'</td>\
                        <td>'+tmp[i].restart+'</td>\
                        <td>'+tmp[i].uptime+'</td>\
                        <td>'+tmp[i].cpu+'</td>\
                        <td>'+tmp[i].mem+'</td>\
                        <td><span onclick="openPath(\''+tmp[i].path+'\')" class="btlink cursor mr20" title="'+tmp[i].path+'">Open</span></td>\
                        <td style="text-align: right;">\
                            '+opt+'<a href="javascript:nodeLog(\''+tmp[i].name+'\')" class="btlink">Log</a> | <a href="javascript:delNode(\''+tmp[i].name+'\')" class="btlink">Delete</a>\
                        </td>\
                    </tr>';
        }

        $("#pmlist").html(tbody);
	});
}



//Get a list of version numbers
function getNodeVersions(){
    var loadT = layer.msg('Getting version list...',{icon:16,time:0,shade: [0.3, '#000']});
    $.get('/plugin?action=a&s=Versions&name=pm2',function(versions){
        layer.close(loadT);


    });

    pm2Post('versions', '', function(data){

    	var rdata = $.parseJSON(data.data);
        var versions = rdata.data;

    	var opt = '';
        for(var i=0;i<versions.list.length;i++){
            if(versions.list[i] == versions.version){
                opt += '<option value="'+versions.list[i]+'" selected="selected">'+versions.list[i]+'</option>';
            }else{
                opt += '<option value="'+versions.list[i]+'">'+versions.list[i]+'</option>';
            }
        }
        var con = '<div class="divtable" style="width: 620px;">\
		                <span>Current version</span><select style="margin-left: 5px;width:100px;" class="bt-input-text" name="versions">'+opt+'</select>\
		                <button style="margin-bottom: 3px;margin-left: 5px;" class="btn btn-success btn-sm" onclick="setNodeVersion()">Switch version</button>\
		                <ul class="help-info-text c7 mtb15">\
		                    <li>The current version is <font style="color:red;">['+versions.version+']</font></li>\
		                    <li>Version switching is global and may affect your running project after switching versions</li>\
		                </ul>\
                   </div>';
        $(".soft-man-con").html(con);
    });
}


//switch version
function setNodeVersion(){
    var version = $("select[name='versions']").val();
    var data = "version="+version;
    pm2Post('set_node_version', data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
        if(rdata.status) {
            getNodeVersions();
        }
    });
}


//get module list
function getModList(){
    var con = '<div class="divtable" style="width: 620px;">\
                <input class="bt-input-text mr5" name="mname" type="text" value="" style="width:240px" placeholder="Module name" />\
                <button class="btn btn-default btn-sm va0" onclick="installMod();">Install</button>\
                <table class="table table-hover" style="margin-top: 10px; max-height: 380px; overflow: auto;">\
                    <thead>\
                        <tr>\
                            <th>Name</th>\
                            <th>Version</th>\
                            <th style="text-align: right;">Action</th>\
                        </tr>\
                    </thead>\
                    <tbody id="modlist"></tbody>\
                </table>\
                <ul class="help-info-text c7 mtb15">\
                    <li>The modules installed here are all installed globally.</li>\
                    <li>Install only to the nodejs version currently in use.</li>\
                </ul>\
            </div>';

    $(".soft-man-con").html(con);

    pm2Post('mod_list', '', function(data){
        var rdata = $.parseJSON(data.data);
        var tbody = '';
        var tmp = rdata['data'];
        for(var i=0;i<tmp.length;i++){
            tbody += '<tr>\
                        <td>'+tmp[i].name+'</td>\
                        <td>'+tmp[i].version+'</td>\
                        <td style="text-align: right;">\
                            <a href="#" class="btlink" onclick="uninstallMod(\''+tmp[i].name+'\')">Uninstall</a>\
                        </td>\
                    </tr>';
        }
        $("#modlist").html(tbody);
    });
}


//Install the module
function installMod(){
    var mname = $("input[name='mname']").val();
    if(!mname){
        layer.msg('Module name cannot be empty!',{icon:2});
        return;
    }

    var data = {mname:mname};
    pm2Post('install_mod', data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
        if(rdata.status) {
            getModList();
        }
    });
}


function uninstallMod(mname){
    safeMessage('Uninstall the module ['+mname+']', 'After uninstalling the ['+mname+'] module, it may affect existing projects, continue?',function(){
        var data = "mname="+mname;
        pm2Post('uninstall_mod', data, function(data){
            var rdata = $.parseJSON(data.data);
            layer.msg(rdata.msg,{icon:rdata.status?1:2});
            if(rdata.status) {
                getModList();
            }
        });
    });
}

function addNode(){
	var data = {path:$("input[name='path']").val(),pname:$("input[name='pname']").val(),run:$("input[name='run']").val()}
	if(!data.path || !data.pname || !data.run){
        layer.msg('The form is incomplete, please check!',{icon:2});
        return;
    }

    pm2Post('add', data, function(data){
    	var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
        pm2List();
    });
}

function delNode(pname){
    safeMessage('Delete item ['+pname+']', 'After deleting the ['+pname+'] item, the item will not be accessible, continue?',function(){
        var data = "pname="+pname;
        pm2Post('delete', data, function(data){
        	var rdata = $.parseJSON(data.data);
	        layer.msg(rdata.msg,{icon:rdata.status?1:2});
	        pm2List();
        });
    });
}

function nodeStop(pname){
	var data = 'pname=' + pname;
	pm2Post('stop', data, function(data){
    	var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
        pm2List();
    });
}

function nodeStart(pname){
	var data = 'pname=' + pname;
	pm2Post('start', data, function(data){
    	var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
        pm2List();
    });
}

function pm2RollingLogs(func,pname){
    var args = {'pname':pname}
    _args = JSON.stringify(args);
    pluginRollingLogs('pm2','',func, _args);
}

function nodeLog(pname){
	var html = '';
    html += '<button onclick="pm2RollingLogs(\'node_log_run\',\''+pname+'\')" class="btn btn-default btn-sm">Run log</button>';
    html += '<button onclick="nodeLogClearRun(\''+pname+'\')" class="btn btn-default btn-sm">Clear run log</button>';
    html += '<button onclick="pm2RollingLogs(\'node_log_err\',\''+pname+'\')" class="btn btn-default btn-sm">Error log</button>';
    html += '<button onclick="nodeLogClearError(\''+pname+'\')" class="btn btn-default btn-sm">Clear error log</button>';

    var loadOpen = layer.open({
        type: 1,
        title: 'Log',
        area: '240px',
        content:'<div class="change-default pd20">'+html+'</div>'
    });
}


function nodeLogClearRun(pname){
    var data = 'pname=' + pname;
    pm2Post('node_log_clear_run', data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
    });
}

function nodeLogClearError(pname){
    var data = 'pname=' + pname;
    pm2Post('node_log_clear_err', data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
    });
}

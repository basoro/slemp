setTimeout(function(){
	getSshInfo();
},500);

setTimeout(function(){
	showAccept(1);
},1000);

setTimeout(function(){
	getLogs(1);
},1500);


$(function(){
	// start
	$.post('/firewall/get_www_path',function(data){
		var html ='<a href="javascript:openPath(\''+data['path']+'\');">Log directory</a>\
				<em id="logSize">0KB</em>\
				<button class="btn btn-default btn-sm" onclick="closeLogs();">Empty</button>';
		$('#firewall_weblog').html(html);

		$.post('/files/get_dir_size','path='+data['path'], function(rdata){
			$("#logSize").html(rdata.msg);
		},'json');
	},'json');
	// end
});

function closeLogs(){
	$.post('/files/close_logs','',function(rdata){
		$("#logSize").html(rdata.msg);
		layer.msg('Cleaned up!',{icon:1});
	},'json');
}

$("#firewalldType").change(function(){
	var type = $(this).val();
	var w = '120px';
	var p = 'Port';
	var t = 'Release';
	var m = 'Caption: Support release port range, such as: 3000:3500';
	if(type == 'address'){
		w = '150px';
		p = 'IP address to be blocked';
		t = 'Block';
		m = 'Caption: Supports masking of IP segments, such as: 192.168.0.0/24';
	}
	$("#AcceptPort").css("width",w);
	$("#AcceptPort").attr('placeholder',p);
	$("#toAccept").html(t);
	$("#f-ps").html(m);
});


function getSshInfo(){
	$.post('/firewall/get_ssh_info', '', function(rdata){
		// console.log(rdata);
		var SSHchecked = ''
		if(rdata.status){
			SSHchecked = "<input class='btswitch btswitch-ios' id='sshswitch' type='checkbox' checked><label class='btswitch-btn' for='sshswitch' onclick='setMstscStatus()'></label>";
		} else {
			SSHchecked = "<input class='btswitch btswitch-ios' id='sshswitch' type='checkbox'><label class='btswitch-btn' for='sshswitch' onclick='setMstscStatus()'></label>";
			$("#mstscSubmit").attr('disabled','disabled');
			$("#mstscPort").attr('disabled','disabled');
		}

		$("#in_safe").html(SSHchecked);
		$("#mstscPort").val(rdata.port);
		var isPint = '';
		if(rdata.ping){
			isPing = "<input class='btswitch btswitch-ios' id='noping' type='checkbox'><label class='btswitch-btn' for='noping' onclick='ping(1)'></label>";
		}else{
			isPing = "<input class='btswitch btswitch-ios' id='noping' type='checkbox' checked><label class='btswitch-btn' for='noping' onclick='ping(0)'></label>";
		}
		$("#is_ping").html(isPing);

		// console.log(rdata.firewall_status);
		var fStatus = '';
		if (rdata.firewall_status){
			fStatus = "<input class='btswitch btswitch-ios' id='firewall_status' type='checkbox' checked><label class='btswitch-btn' for='firewall_status' onclick='firewall(1)'></label>";
		}else{
			fStatus = "<input class='btswitch btswitch-ios' id='firewall_status' type='checkbox'><label class='btswitch-btn' for='firewall_status' onclick='firewall(0)'></label>";
		}
		$("#firewall_status").html(fStatus);

	},'json');
}

function mstsc(port) {
	layer.confirm('When changing the remote port, all logged in accounts will be logged out, do you really want to change the remote port?', {title: 'Remote port'}, function(index) {
		var data = "port=" + port;
		var loadT = layer.load({
			shade: true,
			shadeClose: false
		});
		$.post('/firewall/set_ssh_port', data, function(ret) {
			layer.msg(ret.msg,{icon:ret.status?1:2})
			layer.close(loadT);
			getSshInfo();
		},'json');
	});
}

function ping(status){
	var msg = status == 1 ? 'After banning PING, it will not affect the normal use of the server, but the server cannot be pinged. Do you really want to ban PING?' : 'Unblocking PING status may be discovered by hackers on your server, do you really want to unblock it?';
	layer.confirm(msg,{title:'Whether to ban ping',closeBtn:2,btn:['Yes','No'],cancel:function(){
		if(status == 1){
			$("#noping").prop("checked",true);
		} else {
			$("#noping").prop("checked",false);
		}
	}},function(){
		layer.msg('Processing, please wait...',{icon:16,time:20000});
		$.post('/firewall/set_ping','status='+status, function(data) {
			layer.closeAll();
			if (data['status'] == true) {
				if(status == 1){
					layer.msg(data['msg'], {icon: 1});
				} else {
					layer.msg('PING unbanned', {icon: 1});
				}
				setTimeout(function(){window.location.reload();},3000);
			} else {
				layer.msg('Connection failure', {icon: 2});
			}
		},'json');
	},function(){
		if(status == 1){
			$("#noping").prop("checked",true);
		} else {
			$("#noping").prop("checked",false);
		}
	});
}

function firewall(status){
	var msg = status == 1 ? 'Disabling the firewall increases server insecurity, do you really want to disable the firewall?' : 'Turn on the firewall to increase server security!';
	layer.confirm(msg,{title:'Whether to open the firewall!',closeBtn:2,btn:['Yes','No'],cancel:function(){
		if(status == 1){
			$("#firewall_status").prop("checked",true);
		} else {
			$("#firewall_status").prop("checked",false);
		}
	}},function(){
		layer.msg('Processing, please wait...',{icon:16,time:20000});
		$.post('/firewall/set_fw','status='+status, function(data) {
			layer.closeAll();
			if (data['status'] == true) {
				layer.msg(data['msg'], {icon: 1});
				setTimeout(function(){window.location.reload();},3000);
			} else {
				layer.msg('Connection failure', {icon: 2});
			}
		},'json');
	},function(){
		if(status == 1){
			$("#firewall_status").prop("checked",true);
		} else {
			$("#firewall_status").prop("checked",false);
		}
	});
}

function setMstscStatus(){
	status = $("#sshswitch").prop("checked")==true?1:0;
	var msg = status==1?'Disabling the SSH service will also log out all logged in users. ContinueAre you sure you enable SSH service？':'Are you sure you enable SSH service?';
	layer.confirm(msg,{title:'Notif',closeBtn:2,btn:['Yes','No'],cancel:function(){
		if(status == 0){
			$("#sshswitch").prop("checked",false);
		}
		else{
			$("#sshswitch").prop("checked",true);
		}
	}},function(index){
		if(index > 0){
			layer.msg('Processing, please wait...',{icon:16,time:20000});
			$.post('/firewall/set_ssh_status','status='+status,function(rdata){
				// console.log(rdata);
				layer.closeAll();
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
				setTimeout(function(){window.location.reload();},3000);
			},'json');
		}
	},function(){
		if(status == 0){
			$("#sshswitch").prop("checked",false);
		} else {
			$("#sshswitch").prop("checked",true);
		}
	});
}

function showAccept(page,search) {
	search = search == undefined ? '':search;
	var loadT = layer.load();
	$.post('/firewall/get_list','limit=10&p=' + page+"&search="+search, function(data) {
		layer.close(loadT);
		var body = '';
		for (var i = 0; i < data.data.length; i++) {
			var status = '';
			switch(data.data[i].status){
				case 0:
					status = 'Unused';
					break;
				case 1:
					status = 'No access to the external network';
					break;
				default:
					status = 'Normal';
					break;
			}
			body += "<tr>\
						<td><em class='dlt-num'>" + data.data[i].id + "</em></td>\
						<td>" + (data.data[i].port.indexOf('.') == -1?'Release port'+':['+data.data[i].port+']':'Block IP'+':['+data.data[i].port+']') + "</td>\
						<td>" + status + "</td>\
						<td>" + data.data[i].addtime + "</td>\
						<td>" + data.data[i].ps + "</td>\
						<td class='text-right'><a href='javascript:;' class='btlink' onclick=\"delAcceptPort(" + data.data[i].id + ",'" + data.data[i].port + "')\">Del</a></td>\
					</tr>";
		}
		$("#firewallBody").html(body);
		$("#firewallPage").html(data.page);
	},'json');
}

function addAcceptPort(){
	var type = $("#firewalldType").val();
	var port = $("#AcceptPort").val();
	var ps = $("#Ps").val();
	var action = "add_drop_address";
	if(type == 'port'){
		ports = port.split(':');
		for(var i=0;i<ports.length;i++){
			if(isNaN(ports[i]) || ports[i] < 1 || ports[i] > 65535 ){
				layer.msg('Invalid port range!',{icon:5});
				return;
			}
		}
		action = "add_accept_port";
	}


	if(ps.length < 1){
		layer.msg('Descriptions cannot be empty!',{icon:2});
		$("#Ps").focus();
		return;
	}
	var loadT = layer.msg('Adding, please wait...',{icon:16,time:0,shade: [0.3, '#000']})
	$.post('/firewall/'+action,'port='+port+"&ps="+ps+'&type='+type,function(rdata){
		layer.close(loadT);
		if(rdata.status == true || rdata.status == 'true'){
			layer.msg(rdata.msg,{icon:1});
			showAccept(1);
			$("#AcceptPort").val('');
			$("#Ps").val('');
		}else{
			layer.msg(rdata.msg,{icon:2});
		}

		$("#AcceptPort").attr('value','');
		$("#Ps").attr('value','');
	},'json');
}

function delAcceptPort(id, port) {
	var action = "del_drop_address";
	if(port.indexOf('.') == -1){
		action = "del_accept_port";
	}

	layer.confirm(lan.get('confirm_del',[port]), {title: 'Delete firewall rules',closeBtn:2,btn:['Yes','No']}, function(index) {
		var loadT = layer.msg('Deleting, please wait...',{icon:16,time:0,shade: [0.3, '#000']})
		$.post("/firewall/"+action, "id=" + id + "&port=" + port, function(ret) {
			layer.close(loadT);
			layer.msg(ret.msg,{icon:ret.status?1:2})
			showAccept(1);
		},'json');
	});
}

function getLogs(page,search) {
	search = search == undefined ? '':search;
	var loadT = layer.load();
	$.post('/firewall/get_log_list','limit=10&p=' + page+"&search="+search, function(data) {
		layer.close(loadT);
		var body = '';
		for (var i = 0; i < data.data.length; i++) {
			body += "<tr>\
						<td><em class='dlt-num'>" + data.data[i].id + "</em></td>\
						<td>" + data.data[i].type + "</td>\
						<td>" + data.data[i].log + "</td>\
						<td>" + data.data[i].addtime + "</td>\
					</tr>";
		}
		$("#logsBody").html(body);
		$("#logsPage").html(data.page);
	},'json');
}

function delLogs(){
	layer.confirm('About to clear the panel log, continue?',{title:'Clear log',closeBtn:2,btn:['Yes','No']},function(){
		var loadT = layer.msg('Cleaning up, please wait...',{icon:16});
		$.post('/firewall/del_panel_logs','',function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			getLogs(1);
		},'json');
	});
}

$('input[name="webname"]').change(function(){
	var webname = $(this).val();
	$('.btn_webname').removeAttr('disabled');
	$('.btn_webname').unbind().click(function(){
		$.post('/config/set_webname','webname='+webname, function(rdata){
			showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
		},'json');
	});
});


$('input[name="host_ip"]').change(function(){
	var host_ip = $(this).val();
	$('.btn_host_ip').removeAttr('disabled');
	$('.btn_host_ip').unbind().click(function(){
		$.post('/config/set_ip','host_ip='+host_ip, function(rdata){
			showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
		},'json');
	});
});

$('input[name="port"]').change(function(){
	var port = $(this).val();
	$('.btn_port').removeAttr('disabled');
	$('.btn_port').unbind().click(function(){
		$.post('/config/set_port','port='+port, function(rdata){
			showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
		},'json');
	});
});

$('input[name="sites_path"]').change(function(){
	var sites_path = $(this).val();
	$('.btn_sites_path').removeAttr('disabled');
	$('.btn_sites_path').unbind().click(function(){
		$.post('/config/set_www_dir','sites_path='+sites_path, function(rdata){
			showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
		},'json');
	});
});


$('input[name="backup_path"]').change(function(){
	var backup_path = $(this).val();
	$('.btn_backup_path').removeAttr('disabled');
	$('.btn_backup_path').unbind().click(function(){
		$.post('/config/set_backup_dir','backup_path='+backup_path, function(rdata){
			showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
		},'json');
	});
});


$('input[name="bind_domain"]').change(function(){
	var domain = $(this).val();
	$('.btn_bind_domain').removeAttr('disabled');
	$('.btn_bind_domain').unbind().click(function(){
		$.post('/config/set_panel_domain','domain='+domain, function(rdata){
			showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
		},'json');
	});
});

$('input[name="bind_ssl"]').click(function(){
	var open_ssl = $(this).prop("checked");
	$.post('/config/set_panel_ssl',{}, function(rdata){
		showMsg(rdata.msg,function(){window.location.reload();},{icon:rdata.status?1:2},2000);
	},'json');
});

/** op **/


function closePanel(){
	layer.confirm('Closing the panel will prevent you from accessing the panel, do you really want to close the Linux panel?',{title:'Close panel',closeBtn:2,icon:13,cancel:function(){
		$("#closePl").prop("checked",false);
	}}, function() {
		$.post('/config/close_panel','',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			setTimeout(function(){
				window.location.reload();
			},1000);
		},'json');
	},function(){
		$("#closePl").prop("checked",false);
	});
}

function debugMode(){
	var loadT = layer.msg('Sending request, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config/open_debug', {}, function (rdata) {
        layer.close(loadT);
        showMsg(rdata.msg, function(){
			window.location.reload();
		} ,{icon:rdata.status?1:2}, 1000);
    },'json');
}


function modifyAuthPath() {
    var auth_path = $("#admin_path").val();
    layer.open({
        type: 1,
        area: "500px",
        title: "Modify security entry",
        closeBtn: 1,
        shift: 5,
        btn:['Submit','Cancel'],
        shadeClose: false,
        content: '<div class="bt-form bt-form pd20">\
                    <div class="line ">\
                        <span class="tname">entry address</span>\
                        <div class="info-r">\
                            <input name="auth_path_set" class="bt-input-text mr5" type="text" style="width: 311px" value="' + auth_path + '">\
                        </div>\
                    </div>\
                </div>',
        yes:function(index){
        	var auth_path = $("input[name='auth_path_set']").val();
		    if (auth_path == '/' || auth_path == ''){
		    	layer.confirm('Warning, closing the security entrance is equivalent to directly exposing your background address to the external network, which is very dangerous. Do you really want to change it like this?',{title:'Security Entry Modification',closeBtn:1,icon:13,
		    	cancel:function(){
				}}, function() {
					var loadT = layer.msg(lan.config.config_save, { icon: 16, time: 0, shade: [0.3, '#000'] });
				    $.post('/config/set_admin_path', { admin_path: auth_path }, function (rdata) {
				    	showMsg(rdata.msg, function(){
				    		layer.close(index);
				    		layer.close(loadT);
				    		$("#admin_path").val(auth_path);
				    	},{ icon: rdata.status ? 1 : 2 }, 2000);
					},'json');
				});
		    	return;
		    } else {
		    	var loadT = layer.msg(lan.config.config_save, { icon: 16, time: 0, shade: [0.3, '#000'] });
			    $.post('/config/set_admin_path', { admin_path: auth_path }, function (rdata) {
			    	showMsg(rdata.msg, function(){
			    		layer.close(index);
			    		layer.close(loadT);
			    		$("#admin_path").val(auth_path);
			    	},{ icon: rdata.status ? 1 : 2 }, 2000);
			    },'json');
		    }
        }
    });
}

function setPassword(a) {
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		if(p1 == "" || p1.length < 8) {
			layer.msg('The panel password cannot be less than 8 characters!', {icon: 2});
			return
		}

		var checks = ['admin888','123123123','12345678','45678910','87654321','asdfghjkl','password','qwerqwer'];
		pchecks = 'abcdefghijklmnopqrstuvwxyz1234567890';
		for(var i=0;i<pchecks.length;i++){
			checks.push(pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]);
		}

		cps = p1.toLowerCase();
		var isError = "";
		for(var i=0;i<checks.length;i++){
			if(cps == checks[i]){
				isError += '['+checks[i]+'] ';
			}
		}

		if(isError != ""){
			layer.msg('The panel password cannot be a weak password'+isError,{icon:5});
			return;
		}

		if(p1 != p2) {
			layer.msg('The two entered passwords do not match', {icon: 2});
			return;
		}
		$.post("/config/set_password", "password1=" + encodeURIComponent(p1) + "&password2=" + encodeURIComponent(p2), function(b) {
			if(b.status) {
				layer.closeAll();
				layer.msg(b.msg, {icon: 1});
			} else {
				layer.msg(b.msg, {icon: 2});
			}
		},'json');
		return;
	}
	layer.open({
		type: 1,
		area: "290px",
		title: 'Change Password',
		closeBtn: 1,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'>\
				<div class='line'>\
					<span class='tname'>Password</span>\
					<div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='New password' style='width:100%'/></div>\
				</div>\
				<div class='line'>\
					<span class='tname'>Re-Password</span>\
					<div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='Re-Password' style='width:100%' /></div>\
				</div>\
				<div class='bt-form-submit-btn'>\
					<span style='float: left;' title='Random code' class='btn btn-default btn-sm' onclick='randPwd(10)'>Random</span>\
					<button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">Cancel</button>\
					<button type='button' class='btn btn-success btn-sm' onclick=\"setPassword(1)\">Save</button>\
				</div>\
			</div>"
	});
}


function randPwd(){
	var pwd = randomStrPwd(12);
	$("#p1").val(pwd);
	$("#p2").val(pwd);
	layer.msg(lan.bt.pass_rep_ps,{time:2000})
}

function setUserName(a) {
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		if(p1 == "" || p1.length < 3) {
			layer.msg('Username length cannot be less than 3 characters', {icon: 2});
			return;
		}
		if(p1 != p2) {
			layer.msg('The usernames entered twice do not match', {icon: 2});
			return;
		}
		$.post("/config/set_name", "name1=" + encodeURIComponent(p1) + "&name2=" + encodeURIComponent(p2), function(b) {
			if(b.status) {
				layer.closeAll();
				layer.msg(b.msg, {icon: 1});
				$("input[name='username_']").val(p1)
			} else {
				layer.msg(b.msg, {icon: 2});
			}
		},'json');
		return
	}
	layer.open({
		type: 1,
		area: "290px",
		title: 'Modify Panel Username',
		closeBtn: 1,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'>\
			<div class='line'><span class='tname'>Username</span>\
				<div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='Username' style='width:100%'/></div>\
			</div>\
			<div class='line'>\
				<span class='tname'>Re-Username</span>\
				<div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='Re-Username' style='width:100%'/></div>\
			</div>\
			<div class='bt-form-submit-btn'>\
				<button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">Cancel</button>\
				<button type='button' class='btn btn-success btn-sm' onclick=\"setUserName(1)\">Submit</button>\
			</div>\
		</div>"
	})
}

function syncDate(){
	var loadT = layer.msg('Synchronizing time...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/sync_date','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		setTimeout(function(){window.location.reload();},1500);
	},'json');
}


function setIPv6() {
    var loadT = layer.msg('Configuring, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config/set_ipv6_status', {}, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, {icon:rdata.status?1:2});
        setTimeout(function(){window.location.reload();},5000);
    },'json');
}


function setPanelSSL(){
	var status = $("#sshswitch").prop("checked")==true?1:0;
	var msg = $("#panelSSL").attr('checked')?'After closing SSL, you must use the http protocol to access the panel, continue?':'<a style="font-weight: bolder;font-size: 16px;">Danger! Don\'t open this function if you don\'t understand it!</a>\
	<li style="margin-top: 12px;color:red;">You must use and understand this feature before deciding whether to enable it!</li>\
	<li>The panel SSL is a self-signed certificate, which is not trusted by the browser, and it is normal to show that it is insecure</li>\
	<li>After opening, the panel cannot be accessed, you can click the link below to understand the solution</li>\
	<p style="margin-top: 10px;">\
		<input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">I have learned the details and am willing to take the risk</label>\
	</p>';
	layer.confirm(msg,{title:'Settings Panel SSL',closeBtn:1,icon:3,area:'550px',cancel:function(){
		if(status == 0){
			$("#panelSSL").prop("checked",false);
		}
		else{
			$("#panelSSL").prop("checked",true);
		}
	}},function(){
		if(window.location.protocol.indexOf('https') == -1){
			if(!$("#checkSSL").prop('checked')){
				layer.msg(lan.config.ssl_ps,{icon:2});
				return false;
			}
		}
		var loadT = layer.msg('Installing and setting up the SSL components, this will take a few minutes...',{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/config/set_panel_ssl','',function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			if(rdata.status === true){
				$.post('/system/restart','',function (rdata) {
                    layer.close(loadT);
                    layer.msg(rdata.msg);
                    setTimeout(function(){
						window.location.href = ((window.location.protocol.indexOf('https') != -1)?'http://':'https://') + window.location.host + window.location.pathname;
					},3000);
                },'json');
			}
		},'json');
	},function(){
		if(status == 0){
			$("#panelSSL").prop("checked",false);
		}
		else{
			$("#panelSSL").prop("checked",true);
		}
	});
}

function setNotifyApi(tag, obj){
	var enable = $(obj).prop("checked");
	console.log(tag,obj,enable);
	$.post('/config/set_notify_enable', {'tag':tag, 'enable':enable},function(rdata){
		showMsg(rdata.msg, function(){
			if (rdata.status){}
		} ,{icon:rdata.status?1:2}, 1000);
	},'json');
}

function getTgbot(){
	var loadT = layer.msg('Getting TgBot information...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/get_notify',{},function(data){
		layer.close(loadT);

		var app_token = '';
		var chat_id = '';

		if (data.status){
			if (typeof(data['data']['tgbot']) !='undefined'){
				app_token = data['data']['tgbot']['data']['app_token'];
				chat_id = data['data']['tgbot']['data']['chat_id'];
			}
		}

		layer.open({
			type: 1,
			area: "500px",
			title: 'Configure TgBot configuration',
			closeBtn: 1,
			shift: 5,
			btn:["Yes","No","Test"],
			shadeClose: false,
			content: "<div class='bt-form pd20'>\
					<div class='line'>\
						<span class='tname'>APP TOKEN</span>\
						<div class='info-r'><input class='bt-input-text' type='text' name='app_token' value='"+app_token+"' style='width:100%'/></div>\
					</div>\
					<div class='line'>\
						<span class='tname'>CHAT ID</span>\
						<div class='info-r'><input class='bt-input-text' type='text' name='chat_id' value='"+chat_id+"' style='width:100%' /></div>\
					</div>\
				</div>",
			yes:function(index){
				var pdata = {};
				pdata['app_token'] = $('input[name="app_token"]').val();
				pdata['chat_id'] = $('input[name="chat_id"]').val();
				$.post('/config/set_notify',{'tag':'tgbot', 'data':JSON.stringify(pdata)},function(rdata){
					showMsg(rdata.msg, function(){
						if (rdata.status){
							layer.close(index);
						}
					},{icon:rdata.status?1:2},2000);
				});
			},

			btn3:function(index){
				var pdata = {};
				pdata['app_token'] = $('input[name="app_token"]').val();
				pdata['chat_id'] = $('input[name="chat_id"]').val();
				$.post('/config/set_notify_test',{'tag':'tgbot', 'data':JSON.stringify(pdata)},function(rdata){
					showMsg(rdata.msg, function(){
						if (rdata.status){
							layer.close(index);
						}
					},{icon:rdata.status?1:2},2000);
				});
				return false;
			}
		});
	});
}

function getPanelSSL(){
	var loadT = layer.msg('Fetching certificate information...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/get_panel_ssl',{},function(cert){
		layer.close(loadT);


		var cert_data = '';
		if (cert['info']){
			cert_data = "<div class='ssl_state_info'><div class='state_info_flex'>\
				<div class='state_item'><span>Certificate brand：</span>\
				<span class='ellipsis_text ssl_issue'>"+cert['info']['issuer']+"</span></div>\
				<div class='state_item'><span>Expire date：</span>\
				<span class='btlink ssl_endtime'>"+cert['info']['endtime']+" days left to expire</span></div>\
				</div>\
				<div class='state_info_flex'>\
				<div class='state_item'><span>Domain name：</span>\
				<span class='ellipsis_text ssl_subject'>"+cert['info']['subject']+"</span></div>\
				<div class='state_item'>\
					<span>Force HTTPS：</span>\
					<span class='switch'>\
						<input class='btswitch btswitch-ios' id='toHttps' type='checkbox' "+cert['is_https']+">\
						<label class='btswitch-btn set_panel_http_to_https' for='toHttps'></label>\
					</span>\
				</div>\
			</div></div>";
		}

		var certBody = '<div class="tab-con">\
			<div class="myKeyCon ptb15">\
				'+cert_data+'\
				<div class="custom_certificate_info">\
					<div class="ssl-con-key pull-left mr20">Key (KEY)<br>\
						<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
					</div>\
					<div class="ssl-con-key pull-left">Certificate (PEM format)<br>\
						<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
					</div>\
				</div>\
				<div class="ssl-btn pull-left mtb15" style="width:100%">\
					<button class="btn btn-success btn-sm save-panel-ssl">Save</button>\
					<button class="btn btn-success btn-sm del-panel-ssl">Delete</button>\
					<button class="btn btn-success btn-sm apply-lets-ssl">Apply for a Lets certificate</button>\
				</div>\
			</div>\
			<ul class="help-info-text c7 pull-left">\
				<li>Paste your *.key and *.pem content, then save.</li>\
				<li>If the browser prompts that the certificate chain is incomplete, please check whether the PEM certificate is spliced correctly</li><li>PEM format certificate = domain name certificate.crt + root certificate (root_bundle).crt</li>\
			</ul>\
		</div>'
		layer.open({
			type: 1,
			area: "600px",
			title: 'Custom Panel Certificate',
			closeBtn: 1,
			shift: 5,
			shadeClose: false,
			content:certBody,
			success:function(layero, layer_id){

				$('.save-panel-ssl').click(function(){
					var data = {
						privateKey:$("#key").val(),
						certPem:$("#csr").val()
					}
					var loadT = layer.msg('Installing and setting up the SSL components, this will take a few minutes...',{icon:16,time:0,shade: [0.3, '#000']});
					$.post('/config/save_panel_ssl',data,function(rdata){
						layer.close(loadT);
						if(rdata.status){
							layer.closeAll();
						}
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
					},'json');
				});

				$('.del-panel-ssl').click(function(){
					var loadT = layer.msg('Removing SSL...',{icon:16,time:0,shade: [0.3, '#000']});
					$.post('/config/del_panel_ssl',data,function(rdata){
						layer.close(loadT);
						if(rdata.status){
							layer.closeAll();
						}
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
					},'json');
				});

				$('.set_panel_http_to_https').click(function(){
					var https = $('#toHttps').prop('checked');
					$.post('/config/set_panel_http_to_https',{'https':https},function(rdata){
						layer.close(loadT);
						if(rdata.status){
							layer.closeAll();
						}
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
					},'json');
				});

				$('.apply-lets-ssl').click(function(){
					showSpeedWindow('Currently applying...', 'site.get_let_logs', function(layers,index){
						$.post('/config/apply_panel_let_ssl',{},function(rdata){
							layer.close(loadT);
							if(rdata.status){
								layer.close(index);
								var tdata = rdata['data'];
								$('.ssl_issue').text(tdata['info']['issuer']);
								$('.ssl_endtime').text("Remaining "+tdata['info']['endtime']+" days due");
								$('.ssl_subject').text(tdata['info']['subject']);

								$('textarea[name="key"]').val(tdata['info']['privateKey']);
								$('textarea[name="csr"]').val(tdata['info']['certPem']);
							}
							layer.msg(rdata.msg,{icon:rdata.status?1:2});
						},'json');
					});
				});
			}
		});
	},'json');
}


function removeTempAccess(id){
	$.post('/config/remove_temp_login', {id:id}, function(rdata){
		showMsg(rdata.msg, function(){
			setTempAccessReq();
		},{ icon: rdata.status ? 1 : 2 }, 2000);
	},'json');
}

function getTempAccessLogsReq(id){
	$.post('/config/get_temp_login_logs', {id:id}, function(rdata){
		var tbody = '';
		for (var i = 0; i < rdata.data.length; i++) {

			tbody += '<tr>';
			tbody += '<td>' + (rdata.data[i]['type']) +'</td>';
			tbody += '<td>' + rdata.data[i]['addtime'] +'</td>';
			tbody += '<td>'+ rdata.data[i]['log'] +'</td>';
			tbody += '</tr>';
		}
		$('#logs_list').html(tbody);

	},'json');
}

function getTempAccessLogs(id){

	layer.open({
		area: ['700px', '250px'],
		title: 'Temporary Authorization Management',
		closeBtn:1,
		shift: 0,
		type: 1,
		content: "<div class=\"pd20\">\
					<button class=\"btn btn-success btn-sm refresh_log\">Refresh log</button>\
					<div class=\"divtable mt10\">\
						<table class=\"table table-hover\">\
							<thead>\
								<tr><th>Type</th><th>Time</th><th>Log</th></tr>\
							</thead>\
							<tbody id=\"logs_list\"></tbody>\
						</table>\
					</div>\
				</div>",
		success:function(){
			getTempAccessLogsReq(id);
			$('.refresh_log').click(function(){
				getTempAccessLogsReq(id);
			});
		}
	});
}

function setTempAccessReq(page){
	if (typeof(page) == 'undefined'){
		page = 1;
	}

	$.post('/config/get_temp_login', {page:page}, function(rdata){
		if ( typeof(rdata.status) !='undefined' && !rdata.status){
			showMsg(rdata.msg,function(){
				layer.closeAll();
			},{icon:2}, 2000);
			return;
		}

		var tbody = '';
		for (var i = 0; i < rdata.data.length; i++) {

			tbody += '<tr>';
			tbody += '<td>' + (rdata.data[i]['login_addr']||'Not logged in') +'</td>';

			tbody += '<td>';
			switch (parseInt(rdata.data[i]['state'])) {
				case 0:
					tbody += '<a style="color:green;">To be used</a>';
					break;
				case 1:
					tbody += '<a style="color:brown;">Used</a>';
					break;
				case -1:
					tbody += '<a>Expired</a>';
					break;
			}
			tbody += '</td>';

			tbody += '<td>' + (getLocalTime(rdata.data[i]['login_time'])||'Not logged in') +'</td>';
			tbody += '<td>' + getLocalTime(rdata.data[i]['expire']) +'</td>';

			tbody += '<td>';

			if (rdata.data[i]['state'] == '1' ){
				tbody += '<a class="btlink" onclick="getTempAccessLogs(\''+rdata.data[i]['id']+'\')">Log</a>';
			} else{
				tbody += '<a class="btlink" onclick="removeTempAccess(\''+rdata.data[i]['id']+'\')">Del</a>';
			}

			tbody += '</td>';

			tbody += '</tr>';
		}

		$('#temp_login_view_tbody').html(tbody);
		$('.temp_login_view_page').html(rdata.page);
	},'json');
}

function setStatusCode(o){
	var code = $(o).data('code');
    layer.open({
        type: 1,
        area: ['420px', '220px'],
        title: "Set the response status when not authenticated",
        closeBtn: 1,
        shift: 5,
        btn:['Submit','Cancel'],
        shadeClose: false,
        content: '<div class="bt-form bt-form pd20">\
                    <div class="line">\
                        <span class="tname">Corresponding state</span>\
                        <div class="info-r">\
                            <select class="bt-input-text mr5" name="status_code" style="width: 250px;"></select>\
                        </div>\
                    </div>\
                    <ul class="help-info-text c7"><li style="color: red;">Response for not logged in and incorrectly entered security entry, used to hide panel features</li></ul>\
                </div>',
        success:function(){
        	var msg_list = [
        		{'code':'0','msg':'Default - Security Entrance Error Prompt'},
        		{'code':'403','msg':'403 - Access Denied'},
        		{'code':'404','msg':'404 - Page does not exist'},
        		{'code':'416','msg':'416 - Invalid request'},
        		{'code':'408','msg':'408 - Client timeout'},
        		{'code':'400','msg':'400 - Client request error'},
        		{'code':'401','msg':'401 - Unauthorized access'},
        	];

        	var tbody = '';
        	for(i in msg_list){
        		if (msg_list[i]['code'] == code){
        			tbody += '<option value="'+msg_list[i]['code']+'" selected>'+msg_list[i]['msg']+'</option>';
        		} else{
        			tbody += '<option value="'+msg_list[i]['code']+'">'+msg_list[i]['msg']+'</option>';
        		}

        	}
        	$('select[name="status_code"]').append(tbody);
        },
        yes:function(index){
		    var loadT = layer.msg("Response status when unauthenticated is being set", { icon: 16, time: 0, shade: [0.3, '#000'] });
		    var status_code = $('select[name="status_code"]').val();
		    $.post('/config/set_status_code', { status_code: status_code }, function (rdata) {
		    	showMsg(rdata.msg, function(){
		    		layer.close(index);
		    		layer.close(loadT);
		    		location.reload();
		    	},{ icon: rdata.status ? 1 : 2 }, 2000);
		    },'json');
        }
    });
}

function setTempAccess(){
	layer.open({
		area: ['700px', '250px'],
		title: 'Temporary Authorization Management',
		closeBtn:1,
		shift: 0,
		type: 1,
		content: "<div class=\"login_view_table pd20\">\
					<button class=\"btn btn-success btn-sm create_temp_login\" >Temporary Access Authorization</button>\
					<div class=\"divtable mt10\">\
						<table class=\"table table-hover\">\
							<thead>\
								<tr><th>Login IP</th><th>Status</th><th>Login time</th><th>Expired</th><th style=\"text-align:right;\">Action</th></tr>\
							</thead>\
							<tbody id=\"temp_login_view_tbody\"></tbody>\
						</table>\
						<div class=\"temp_login_view_page page\"></div>\
					</div>\
				</div>",
		success:function(){
			setTempAccessReq();

			$('.create_temp_login').click(function(){
				layer.confirm('<span style="color:red">Note 1: Misuse of temporary grants can lead to security risks. </br>Note 2: Do not publish temporary authorized connections in public places</span></br>A temporary authorized connection will be created soon, continue?',
				{
					title:'Risk warning',
					closeBtn:1,
					icon:13,
				}, function(create_temp_login_layer) {
					$.post('/config/set_temp_login', {}, function(rdata){
						layer.close(create_temp_login_layer);
						setTempAccessReq();
						layer.open({
							area: '570px',
							title: 'Create temporary authorization',
							shift: 0,
							type: 1,
							content: "<div class=\"bt-form create_temp_view pd15\">\
									<div class=\"line\">\
										<span class=\"tname\">Temporary authorized address</span>\
										<div>\
											<textarea id=\"temp_link\" class=\"bt-input-text mr20\" style=\"margin: 0px;width: 500px;height: 50px;line-height: 19px;\"></textarea>\
										</div>\
									</div>\
									<div class=\"line\"><button type=\"submit\" class=\"btn btn-success btn-sm btn-copy-temp-link\" data-clipboard-text=\"\">Copy address</button></div>\
									<ul class=\"help-info-text c7 ptb15\">\
										<li>The temporary authorization is valid for use within 1 hour after it is generated. It is a one-time authorization and expires immediately after use</li>\
										<li>After using the temporary authorization to log in to the panel, you have all the permissions on the panel within 1 hour, please do not publish the temporary authorization connection in public places</li>\
										<li>The authorized connection information is only displayed here once, if you forget it before use, please regenerate</li>\
									</ul>\
								</div>",
							success:function(){
								var temp_link = "".concat(location.origin, "/login?tmp_token=").concat(rdata.token);
								$('#temp_link').val(temp_link);

								copyText(temp_link);
								$('.btn-copy-temp-link').click(function(){
									copyText(temp_link);
								});
							}
						});
					},'json');
				});
			});
		}
	});
}

function setBasicAuthTip(callback){
	var tip = layer.open({
		area: ['500px', '385px'],
		title: 'Enable BasicAuth authentication prompt',
		closeBtn:0,
		shift: 0,
		type: 1,
		content: '<div class="bt-form pd20">\
		<div class="mb15">\
			<h3 class="layer-info-title">Risky operation! Do not enable this function if you do not understand it!</h3>\
		</div>\
		<ul class="help-info-text c7 explain-describe-list pd15">\
			<li style="color: red;">You must use and understand this feature before deciding whether to enable it!</li>\
			<li>After it is turned on, accessing the panel in any way will first require you to enter the BasicAuth username and password</li>\
			<li>After it is turned on, it can effectively prevent the panel from being scanned and found, but it cannot replace the account password of the panel itself</li>\
			<li>Please remember the BasicAuth password, once you forget it, you will not be able to access the panel</li>\
			<li>If you forget the password, you can turn off BasicAuth authentication through the command in SSH</li>\
		</ul>\
		<div class="mt10 plr15 agreement-box" id="checkBasicAuth">\
			<input class="bt-input-text mr5" name="agreement" type="checkbox" value="false" id="agreement_more">\
			<label for="agreement_more"><span>I have learned the details and am willing to take the risk</span></label>\
		</div>\
	</div>',
		btn:["Yes","No"],
		yes:function(l,index){
			is_agree = $('#agreement_more').prop("checked");
			if (is_agree){
				layer.close(tip);
				callback();
			}
			return is_agree;
		},
		btn2: function(index, layero){
		    $('#cfg_basic_auth').prop("checked", false);
		}
	});
}

function setBasicAuth(){

	var basic_auth = $('#cfg_basic_auth').prop("checked");
	if (!basic_auth){
		setBasicAuthTip(function(){
			var tip = layer.open({
				area: ['500px', '385px'],
				title: 'Configure BasicAuth authentication',
				closeBtn:1,
				shift: 0,
				type: 1,
				content: '<div class="bt-form pd20">\
			<div class="line">\
				<span class="tname">Username</span>\
				<div class="info-r"><input class="bt-input-text mr5" name="basic_user" type="text" placeholder="Please set username" style="width: 280px;"></div>\
			</div>\
			<div class="line">\
				<span class="tname">Password</span>\
				<div class="info-r"><input class="bt-input-text mr5" name="basic_pwd" type="text" placeholder="Please set a password" style="width: 280px;"></div>\
			</div>\
			<div class="line">\
				<span class="tname"></span>\
				<div class="info-r"><button class="btn btn-success btn-sm save_auth_cfg">Save</button></div>\
			</div>\
			<ul class="help-info-text c7">\
				<li style="color: red;">Note: Please do not use your common password here, it may lead to password leakage!</li>\
				<li>After it is turned on, accessing the panel in any way will first require you to enter the BasicAuth username and password</li>\
				<li>After it is turned on, it can effectively prevent the panel from being scanned and found, but it cannot replace the account password of the panel itself</li>\
				<li>Please keep the BasicAuth password in mind, once you forget it, you will not be able to access the panel</li><li>If you forget the password, you can use the command in SSH to disable BasicAuth authentication</li>\
			</ul>\
		</div>',
				success:function(){
					$('.save_auth_cfg').click(function(){
						var basic_user = $('input[name="basic_user"]').val();
						var basic_pwd = $('input[name="basic_pwd"]').val();
						$.post('/config/set_basic_auth', {'basic_user':basic_user,'basic_pwd':basic_pwd},function(rdata){
							showMsg(rdata.msg, function(){
								window.location.reload();
							} ,{icon:rdata.status?1:2}, 2000);
						},'json');
					});
				},
				cancel:function(){
					$('#cfg_basic_auth').prop("checked", false);
				},
			});
		});
	} else {
	    layer.confirm('After closing the BasicAuth authentication, the panel login will no longer verify the BasicAuth basic authentication, which will lead to a decrease in the security of the panel, continue to operate!',
	    {btn: ['Yes', 'No'], title: "Whether to disable BasicAuth authentication?", icon:13}, function (index) {
	    	var basic_user = '';
			var basic_pwd = '';
			$.post('/config/set_basic_auth', {'is_open':'false'},function(rdata){
				showMsg(rdata.msg, function(){
					layer.close(index);
					window.location.reload();
				} ,{icon:rdata.status?1:2}, 2000);
			},'json');
	    },function(){
	    	$('#cfg_basic_auth').prop("checked", true);
	    });
	}
}

function showPanelApi(){
	$.post('/config/get_panel_token', '', function(rdata){
		var tip = layer.open({
			area: ['500px', '355px'],
			title: 'Configuration Panel API',
			closeBtn:1,
			shift: 0,
			type: 1,
			content: '<div class="bt-form pd20">\
		<div class="line">\
			<span class="tname">Interface key</span>\
			<div class="info-r">\
				<input class="bt-input-text mr5" name="token" type="text" style="width: 310px;" disabled>\
				<button class="btn btn-success btn-xs reset_token" style="margin-left: -50px;">Reset</button>\
			</div>\
		</div>\
		<div class="line">\
			<span class="tname" style="width: 90px; overflow: initial; height: 20px; line-height: 20px;">IP whitelist<br/> (1 per line)</span>\
			<div class="info-r"><textarea class="bt-input-text" name="api_limit_addr" style="width: 310px; height: 80px; line-height: 20px; padding: 5px 8px;"></textarea></div>\
		</div>\
		<div class="line">\
			<span class="tname"></span>\
			<div class="info-r"><button class="btn btn-success btn-sm save_api">Save</button></div>\
		</div>\
		<ul class="help-info-text c7">\
			<li>After the API is enabled, only the IP in the IP whitelist can access the panel API interface</li>\
			<li style="color: red;">Please do not enable it in the production environment, which may increase server security risks;</li>\
		</ul>\
	</div>',
			success:function(layero,index){

				$('input[name="token"]').val(rdata.data.token);
				$('textarea[name="api_limit_addr"]').val(rdata.data.limit_addr);


				$('.reset_token').click(function(){
					layer.confirm('Are you sure you want to reset the current key? <br/><span style="color: red; ">After resetting the key, the associated key product will become invalid. Please add a new key to the product again.</span>',{title:'Reset key',closeBtn:2,icon:13,cancel:function(){
					}}, function() {
						$.post('/config/set_panel_token', {'op_type':"1"},function(rdata){
							showMsg("接口密钥已生成，重置密钥后，已关联密钥产品，将失效，请重新添加新密钥至产品。", function(){
								$('input[name="token"]').val(rdata.data);
							} ,{icon:1}, 2000);
						},'json');
					});
				});

				$('.save_api').click(function(){
					var limit_addr = $('textarea[name="api_limit_addr"]').val();
					$.post('/config/set_panel_token', {'op_type':"3",'limit_addr':limit_addr},function(rdata){
						showMsg(rdata.msg, function(){
						} ,{icon:rdata.status?1:2}, 2000);
					},'json');
				});
			},
		});
	},'json');
}


function setPanelApi(){
	var cfg_panel_api = $('#cfg_panel_api').prop("checked");
	$.post('/config/set_panel_token', {'op_type':"2"},function(rdata){
		showMsg(rdata.msg, function(){
			if (rdata.status){
				showPanelApi();
			}
		} ,{icon:rdata.status?1:2}, 1000);
	},'json');
}

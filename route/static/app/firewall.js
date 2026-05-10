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
		var html ='<a class="btlink" href="javascript:openPath(\''+data['path']+'\');">Direktori log</a>\
				<em id="logSize">0KB</em>\
				<button class="btn btn-default btn-sm" onclick="closeLogs();">Kosongkan</button>';
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
		layer.msg('Berhasil dibersihkan!',{icon:1});
	},'json');
}

$("#firewalldType").change(function(){
	var type = $(this).val();
	var w = '120px';
	var p = 'port';
	var t = 'release';
	var m = 'Keterangan: Bisa pakai rentang port, misal: 3000:3500';
	if(type == 'address'){
		w = '150px';
		p = 'Alamat IP';
		t = 'block';
		m = 'Keterangan: Bisa blokir segmen IP, misal: 192.168.0.0/24';
	}
	$("#AcceptPort").css("width",w);
	$("#AcceptPort").attr('placeholder',p);
	$("#toAccept").html(t);
	$("#f-ps").html(m);
});


function sshMgr(){

	$.post('/firewall/get_ssh_info', '', function(rdata){
		var ssh_status = rdata.status ? 'checked':'';
		var pass_prohibit_status = rdata.pass_prohibit_status ? 'checked':'';
		var con = '<div class="pd15">\
                <div class="divtable">\
                    <table class="table table-hover waftable">\
                        <thead><tr><th>Nama</th><th width="80">Status</th></tr></thead>\
                        <tbody>\
                            <tr>\
                                <td>Mulai ssh</td>\
                                <td>\
                                    <div class="ssh-item" style="margin-left:0">\
                                        <input class="btswitch btswitch-ios" id="sshswitch" type="checkbox" '+ssh_status+'>\
                                        <label class="btswitch-btn" for="sshswitch" onclick=\'setMstscStatus()\'></label>\
                                    </div>\
                                </td>\
                            </tr>\
                            <tr>\
                                <td>Larang login password</td>\
                                <td>\
                                    <div class="ssh-item" style="margin-left:0">\
                                        <input class="btswitch btswitch-ios" id="pass_status" type="checkbox" '+pass_prohibit_status+'>\
                                        <label class="btswitch-btn" for="pass_status" onclick=\'setSshPassStatus()\'></label>\
                                    </div>\
                                </td>\
                            </tr>\
                        </tbody>\
                    </table>\
                </div>\
            </div>';
        layer.open({
	        type: 1,
	        title: "Manajemen SSH",
	        area: ['300px', '230px'],
	        closeBtn: 1,
	        shadeClose: false,
	        content: '<div id="ssh_list">'+con+'</div>',
	        success:function(){
	        },
	    });

	},'json');
}


function getSshInfo(){
	$.post('/firewall/get_ssh_info', '', function(rdata){
		if(!rdata.status){
			$("#mstscPort").attr('disabled','disabled');
		}

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

		showAccept(1);
		getLogs(1);

	},'json');
}

function mstsc(port) {
	layer.confirm('Kalau ganti port remote, semua akun yang lagi login bakal dikeluarin. Yakin mau ganti port remote？', {title: 'Port remote'}, function(index) {
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
	var msg = status == 1 ? 'Larang PING nggak bakal ganggu server, tapi server jadi nggak bisa di-ping. Yakin mau larang PING?？' : 'Buka PING bisa bikin server gampang ditemuin hacker. Yakin mau buka？';
	layer.confirm(msg,{title:'Larang ping?',closeBtn:2,cancel:function(){
		if(status == 1){
			$("#noping").prop("checked",true);
		} else {
			$("#noping").prop("checked",false);
		}
	}},function(){
		layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:20000});
		$.post('/firewall/set_ping','status='+status, function(data) {
			layer.closeAll();
			if (data['status'] == true) {
				if(status == 1){
					layer.msg(data['msg'], {icon: 1});
				} else {
					layer.msg('PING diaktifkan lagi', {icon: 1});
				}
				setTimeout(function(){window.location.reload();},3000);
			} else {
				layer.msg('Koneksi gagal', {icon: 2});
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
	var msg = status == 1 ? 'Matiin firewall bikin server nggak aman. Yakin mau matiin firewall？' : 'Nyalain firewall biar server makin aman!';
	layer.confirm(msg,{title:'Nyalain firewall!',closeBtn:2,cancel:function(){
		if(status == 1){
			$("#firewall_status").prop("checked",true);
		} else {
			$("#firewall_status").prop("checked",false);
		}
	}},function(){
		layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:20000});
		$.post('/firewall/set_fw','status='+status, function(data) {
			layer.closeAll();
			if (data['status'] == true) {
				layer.msg(data['msg'], {icon: 1});
				setTimeout(function(){window.location.reload();},3000);
			} else {
				layer.msg('Koneksi gagal', {icon: 2});
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
	var msg = status==1?'Kalau matiin layanan SSH, semua user yang lagi login bakal dikeluarin. Lanjut？':'Yakin mau nyalain layanan SSH？';
	layer.confirm(msg,{title:'Peringatan',closeBtn:2,cancel:function(){
		if(status == 0){
			$("#sshswitch").prop("checked",false);
		} else {
			$("#sshswitch").prop("checked",true);
		}
	}},function(index){
		if(index > 0){
			layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:20000});
			$.post('/firewall/set_ssh_status','status='+status,function(rdata){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
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

function setSshPassStatus(){
	status = $("#pass_status").prop("checked")==true?1:0;
	var msg = status==1?'Nyalain login password, lanjut？':'Yakin mau matiin login password?？';
	layer.confirm(msg,{title:'Peringatan',closeBtn:2,cancel:function(){
		if(status == 0){
			$("#pass_status").prop("checked",false);
		} else {
			$("#pass_status").prop("checked",true);
		}
	}},function(index){
		if(index > 0){
			layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:20000});
			$.post('/firewall/set_ssh_pass_status','status='+status,function(rdata){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
			},'json');
		}
	},function(){
		if(status == 0){
			$("#pass_status").prop("checked",false);
		} else {
			$("#pass_status").prop("checked",true);
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
					status = 'Nggak dipake';
					break;
				case 1:
					status = 'Nggak ada jaringan luar';
					break;
				default:
					status = 'Normal';
					break;
			}
			body += "<tr>\
						<td><em class='dlt-num'>" + data.data[i].id + "</em></td>\
						<td>" + (data.data[i].port.indexOf('.') == -1?'Buka port'+':['+data.data[i].port+']':'Blokir IP'+':['+data.data[i].port+']') + "</td>\
						<td>" + status + "</td>\
						<td>" + data.data[i].addtime + "</td>\
						<td>" + data.data[i].ps + "</td>\
						<td class='text-right'><a href='javascript:;' class='btlink' onclick=\"delAcceptPort(" + data.data[i].id + ",'" + data.data[i].port + "')\">Hapus</a></td>\
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
				layer.msg('Rentang port nggak bener!',{icon:5});
				return;
			}
		}
		action = "add_accept_port";
	}


	if(ps.length < 1){
		layer.msg('Keterangan nggak boleh kosong!',{icon:2});
		$("#Ps").focus();
		return;
	}
	var loadT = layer.msg('Lagi ditambahin, tunggu bentar...',{icon:16,time:0,shade: [0.3, '#000']})
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

	layer.confirm(lan.get('confirm_del',[port]), {title: 'Hapus aturan firewall',closeBtn:2}, function(index) {
		var loadT = layer.msg('Lagi dihapus, tunggu bentar...',{icon:16,time:0,shade: [0.3, '#000']})
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
	layer.confirm('Log panel bakal dibersihin, lanjut？',{title:'Bersihkan log',closeBtn:2},function(){
		var loadT = layer.msg('Lagi dibersihin, tunggu bentar...',{icon:16});
		$.post('/firewall/del_panel_logs','',function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			getLogs(1);
		},'json');
	});
}

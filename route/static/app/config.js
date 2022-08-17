$(".set-submit").click(function(){
	var data = $("#set_config").serialize();
	layer.msg('Menyimpan konfigurasi...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/set',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(rdata.status){
			setTimeout(function(){
				window.location.href = ((window.location.protocol.indexOf('https') != -1)?'https://':'http://') + rdata.data.host + window.location.pathname;
			},2500);
		}
	},'json');
});

function closePanel(){
	layer.confirm('Menutup panel akan menyebabkan kehilangan akses ke panel. Apakah Anda benar-benar ingin menutup panel?',{title:'Tutup Panel',closeBtn:2,icon:13,btn:['Submit','Cancel'],cancel:function(){
		$("#closePl").prop("checked",false);
	}}, function() {
		$.post('/config/close_panel','',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			setTimeout(function(){window.location.reload();},1000);
		},'json');
	},function(){
		$("#closePl").prop("checked",false);
	});
}


function modifyAuthPath() {
    var auth_path = $("#admin_path").val();
    btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">Ok</button>";
    layer.open({
        type: 1,
        area: "500px",
        title: "Ubah entri keamanan",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form bt-form pd20 pb70">\
                    <div class="line ">\
                        <span class="tname">Alamat masuk</span>\
                        <div class="info-r">\
                            <input name="auth_path_set" class="bt-input-text mr5" type="text" style="width: 311px" value="'+ auth_path+'">\
                        </div></div>\
                        <div class="bt-form-submit-btn">\
                            <button type="button" class= "btn btn-sm btn-danger" onclick="layer.closeAll()">Tutup</button>\
                            <button type="button" class="btn btn-sm btn-success" onclick="setAuthPath();">Simpan</button>\
                    </div></div>'
    });
}

function setAuthPath() {
    var auth_path = $("input[name='auth_path_set']").val();
    var loadT = layer.msg(lan.config.config_save, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config/set_admin_path', { admin_path: auth_path }, function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
            layer.closeAll();
            $("#admin_path").val(auth_path);
        }
        setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }); }, 200);
    },'json');
}

function setPassword(a) {
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		if(p1 == "" || p1.length < 8) {
			layer.msg('Kata sandi panel tidak boleh kurang dari 8 karakter!', {icon: 2});
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
			layer.msg('Kata sandi panel tidak boleh berupa kata sandi yang lemah'+isError,{icon:5});
			return;
		}

		if(p1 != p2) {
			layer.msg('Kedua kata sandi yang dimasukkan tidak cocok', {icon: 2});
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
		title: 'Ganti password',
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'>\
				<div class='line'>\
					<span class='tname'>Password</span>\
					<div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='Password baru' style='width:100%'/></div>\
				</div>\
				<div class='line'>\
					<span class='tname'>Ulangi Password</span>\
					<div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='Ulangi password baru' style='width:100%' /></div>\
				</div>\
				<div class='bt-form-submit-btn'>\
					<span style='float: left;' title='Kode acak' class='btn btn-default btn-sm' onclick='randPwd(10)'>Random</span>\
					<button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">Tutup</button>\
					<button type='button' class='btn btn-success btn-sm' onclick=\"setPassword(1)\">Simpan</button>\
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
			layer.msg('Nama pengguna harus minimal 3 karakter', {icon: 2});
			return;
		}
		if(p1 != p2) {
			layer.msg('Nama pengguna yang dimasukkan dua kali tidak cocok', {icon: 2});
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
		title: 'Ubah nama pengguna panel',
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'>\
			<div class='line'><span class='tname'>Username</span>\
				<div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='Username baru' style='width:100%'/></div>\
			</div>\
			<div class='line'>\
				<span class='tname'>Ulangi username</span>\
				<div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='Ulangi username baru' style='width:100%'/></div>\
			</div>\
			<div class='bt-form-submit-btn'>\
				<button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">Tutup</button>\
				<button type='button' class='btn btn-success btn-sm' onclick=\"setUserName(1)\">Simpan</button>\
			</div>\
		</div>"
	})
}


function syncDate(){
	var loadT = layer.msg('Waktu sinkronisasi...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/sync_date','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		setTimeout(function(){window.location.reload();},1500);
	},'json');
}


function setIPv6() {
    var loadT = layer.msg('Mengkonfigurasi, harap tunggu...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config/set_ipv6_status', {}, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, {icon:rdata.status?1:2});
        setTimeout(function(){window.location.reload();},5000);
    },'json');
}

function setPanelSSL(){
	var status = $("#sshswitch").prop("checked")==true?1:0;
	var msg = $("#panelSSL").attr('checked')?'Setelah mematikan SSL, Anda harus menggunakan protokol http untuk mengakses panel, lanjutkan??':'<a style="font-weight: bolder;font-size: 16px;">Bahaya! Jangan aktifkan fitur ini jika tidak mengerti!</a>\
	<li style="margin-top: 12px;color:red;">Anda harus menggunakan dan memahami fitur ini sebelum memutuskan apakah akan mengaktifkannya!</li>\
	<li>Panel SSL adalah sertifikat yang ditandatangani sendiri dan tidak dipercaya oleh browser. Adalah normal untuk menampilkan tidak aman</li>\
	<li>Setelah dibuka, panel tidak dapat diakses, Anda dapat mengklik tautan di bawah untuk mendapatkan solusi.</li>\
	<p style="margin-top: 10px;">\
		<input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">Saya tahu detailnya dan bersedia mengambil risiko</label>\
		<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-4689-1-1.html" style="float: right;">Bantuan</a>\
	</p>';
	layer.confirm(msg,{title:'Setup Panel SSL',closeBtn:2,btn:['Yes','No'],icon:3,area:'550px',cancel:function(){
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
		var loadT = layer.msg('Memasang dan menyiapkan komponen SSL, ini akan memakan waktu beberapa menit...',{icon:16,time:0,shade: [0.3, '#000']});
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


function getPanelSSL(){
	var loadT = layer.msg('Mendapatkan informasi sertifikat...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/get_panel_ssl',{},function(cert){
		layer.close(loadT);
		var certBody = '<div class="tab-con">\
			<div class="myKeyCon ptb15">\
				<div class="ssl-con-key pull-left mr20">KEY<br>\
					<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
				</div>\
				<div class="ssl-con-key pull-left">Sertifikat (Format PEM)<br>\
					<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
				</div>\
				<div class="ssl-btn pull-left mtb15" style="width:100%">\
					<button class="btn btn-success btn-sm" onclick="savePanelSSL()">Simpan</button>\
				</div>\
			</div>\
			<ul class="help-info-text c7 pull-left">\
				<li>Rekatkan konten *.key dan *.pem dan simpan.</li>\
				<li>Jika browser meminta bahwa rantai sertifikat tidak lengkap, periksa apakah sertifikat PEM disambung dengan benar.</li><li>Sertifikat format PEM = sertifikat nama domain.crt + sertifikat root (root_bundle).crt</li>\
			</ul>\
		</div>'
		layer.open({
			type: 1,
			area: "600px",
			title: 'Sertifikat Panel Kustom',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content:certBody
		});
	},'json');
}


function savePanelSSL(){
	var data = {
		privateKey:$("#key").val(),
		certPem:$("#csr").val()
	}
	var loadT = layer.msg('Memasang dan menyiapkan komponen SSL, ini akan memakan waktu beberapa menit...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/save_panel_ssl',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.closeAll();
		}
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

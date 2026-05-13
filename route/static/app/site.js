function getWeb(page, search, type_id) {
	var search = $("#SearchValue").prop("value");
	var page = page == undefined ? '1' : page;
	var order = getCookie('order');
	if (order) {
		order = '&order=' + order;
	} else {
		order = '';
	}

	var type = '';
	if (typeof (type_id) == 'undefined') {
		type = '&type_id=-1';
	} else {
		type = '&type_id=' + type_id;
	}

	var sUrl = '/site/list';
	var pdata = 'limit=10&p=' + page + '&search=' + search + order + type;
	var loadT = layer.load();
	$.post(sUrl, pdata, function (data) {
		layer.close(loadT);
		var body = '';
		$("#webBody").html(body);
		for (var i = 0; i < data.data.length; i++) {
			if (data.data[i].status == 'running' || data.data[i].status == '1') {
				var status = "<a href='javascript:;' title='Nonaktifkan situs ini' onclick=\"webStop(" + data.data[i].id + ",'" + data.data[i].name + "')\" class='btn-defsult'><span style='color:rgb(92, 184, 92)'>Berjalan</span><span style='color:rgb(92, 184, 92)' class='glyphicon glyphicon-play'></span></a>";
			} else {
				var status = "<a href='javascript:;' title='Aktifkan situs ini' onclick=\"webStart(" + data.data[i].id + ",'" + data.data[i].name + "')\" class='btn-defsult'><span style='color:red'>Berhenti</span><span style='color:rgb(255, 0, 0);' class='glyphicon glyphicon-pause'></span></a>";
			}

			if (data.data[i].backup_count > 0) {
				var backup = "<a href='javascript:;' class='btlink' onclick=\"getBackup(" + data.data[i].id + ")\">Ada cadangan</a>";
			} else {
				var backup = "<a href='javascript:;' class='btlink' onclick=\"getBackup(" + data.data[i].id + ")\">Belum ada cadangan</a>";
			}
			var web_end_time = (data.data[i].edate == "0000-00-00") ? 'Permanen' : data.data[i].edate;

			var shortwebname = data.data[i].name;
			var shortpath = data.data[i].path;
			if (data.data[i].name.length > 30) {
				shortwebname = data.data[i].name.substring(0, 30) + "...";
			}
			if (data.data[i].path.length > 30) {
				shortpath = data.data[i].path.substring(0, 30) + "...";
			}
			var idname = data.data[i].name.replace(/\./g, '_');

			body = "<tr><td><input type='checkbox' name='id' title='" + data.data[i].name + "' onclick='checkSelect();' value='" + data.data[i].id + "'></td>\
					<td><a class='btlink webtips' href='javascript:;' onclick=\"webEdit(" + data.data[i].id + ",'" + data.data[i].name + "','" + data.data[i].edate + "','" + data.data[i].addtime + "')\" title='" + data.data[i].name + "'>" + shortwebname + "</td>\
					<td>" + status + "</td>\
					<td>" + backup + "</td>\
					<td><a class='btlink' title='Buka folder "+ data.data[i].path + "' href=\"javascript:openPath('" + data.data[i].path + "');\">" + shortpath + "</a></td>\
					<td><a class='btlink setTimes' id='site_"+ data.data[i].id + "' data-ids='" + data.data[i].id + "'>" + web_end_time + "</a></td>\
					<td><a class='btlinkbed' href='javascript:;' data-id='"+ data.data[i].id + "'>" + data.data[i].ps + "</a></td>\
					<td style='text-align:right; color:#bbb'>\
						<a href='javascript:;' class='btlink' onclick=\"webEdit(" + data.data[i].id + ",'" + data.data[i].name + "','" + data.data[i].edate + "','" + data.data[i].addtime + "')\">Atur</a>\
                        | <a href='javascript:;' class='btlink' onclick=\"webDelete('" + data.data[i].id + "','" + data.data[i].name + "')\" title='Hapus situs'>Hapus</a>\
					</td></tr>"

			$("#webBody").append(body);
			//setEdate(data.data[i].id,data.data[i].edate);
			function getDate(a) {
				var dd = new Date();
				dd.setTime(dd.getTime() + (a == undefined || isNaN(parseInt(a)) ? 0 : parseInt(a)) * 86400000);
				var y = dd.getFullYear();
				var m = dd.getMonth() + 1;
				var d = dd.getDate();
				return y + "-" + (m < 10 ? ('0' + m) : m) + "-" + (d < 10 ? ('0' + d) : d);
			}
			$('#webBody').on('click', '#site_' + data.data[i].id, function () {
				var _this = $(this);
				var id = $(this).attr('data-ids');
				laydate.render({
					elem: '#site_' + id
					, min: getDate(1)
					, max: '2099-12-31'
					, vlue: getDate(365)
					, type: 'date'
					, lang: 'en'
					, format: 'yyyy-MM-dd'
					, trigger: 'click'
					, btns: ['permanen', 'konfirmasi']
					, theme: '#20a53a'
					, done: function (dates) {
						if (_this.html() == 'Permanen') {
							dates = '0000-00-00';
						}
						var loadT = layer.msg(lan.site.saving_txt, { icon: 16, time: 0, shade: [0.3, "#000"] });
						$.post('/site/set_end_date', 'id=' + id + '&edate=' + dates, function (rdata) {
							layer.close(loadT);
							layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
						}, 'json');
					}
				});
				this.click();
			});
		}
		if (body.length < 10) {
			body = "<tr><td colspan='9'>Belum ada data situs</td></tr>";
			// $(".dataTables_paginate").hide();
			$("#webBody").html(body);
		}

		$(".btn-more").hover(function () {
			$(this).addClass("open");
		}, function () {
			$(this).removeClass("open");
		});

		$("#webPage").html(data.page);

		$(".btlinkbed").click(function () {
			var dataid = $(this).attr("data-id");
			var databak = $(this).text();
			if (databak == 'kosong') databak = '';
			$(this).hide().after("<input class='baktext' type='text' data-id='" + dataid + "' data-page='" + page + "' name='bak' value='" + databak + "' placeholder='Catatan' onblur='getBakPost(\"sites\")' />");
			$(".baktext").focus();
		});

		readerTableChecked();
	}, 'json');
}


function getBakPost(b) {
	$(".baktext").hide().prev().show();
	var id = $(".baktext").attr("data-id");
	var page = $(".baktext").attr("data-page");
	var a = $(".baktext").val();
	if (a == "") {
		a = 'null';
	}
	setWebPs(b, id, a, page);
	$("a[data-id='" + id + "']").html(a);
	$(".baktext").remove();
}

function setWebPs(b, id, ps, page) {
	var d = layer.load({ shade: true, shadeClose: false });
	var ps = 'ps=' + ps;
	$.post('/site/set_ps', 'id=' + id + "&" + ps, function (data) {
		if (data['status']) {
			getWeb(page);
			layer.closeAll();
			layer.msg('Berhasil diubah!', { icon: 1 });
		} else {
			layer.closeAll();
			layer.msg('Gagal mengubah!', { icon: 2 });
		}
	}, 'json');
}

function webAdd(type) {
	loading = layer.msg('Memeriksa status layanan OpenResty!', { icon: 16, time: 0, shade: [0.3, "#000"] })
	$.post('/site/check_web_status', function (data) {
		layer.close(loading);
		if (data.status) {
			webAddPage(type)
		} else {
			layer.msg(data.msg, { icon: 0, time: 3000, shade: [0.3, "#000"] })
		}
	}, 'json');
}

function webAddPage(type) {

	if (type == 1) {
		var array;
		var str = "";
		var domainlist = '';
		var domain = array = $("#mainDomain").val().replace('http://', '').replace('https://', '').split("\n");
		var webport = [];
		var checkDomain = domain[0].split('.');
		if (checkDomain.length < 1) {
			layer.msg(lan.site.domain_err_txt, { icon: 2 });
			return;
		}
		for (var i = 1; i < domain.length; i++) {
			domainlist += '"' + domain[i] + '",';
		}

		webport = domain[0].split(":")[1];
		if (webport == undefined) {
			webport = "80";
		}

		domainlist = domainlist.substring(0, domainlist.length - 1);
		domain = '{"domain":"' + domain[0] + '","domainlist":[' + domainlist + '],"count":' + domain.length + '}';
		var loadT = layer.msg(lan.public.the_get, { icon: 16, time: 0, shade: [0.3, "#000"] })
		var data = $("#addweb").serialize() + "&port=" + webport + "&webinfo=" + domain;

		$.post('/site/add', data, function (ret) {
			if (ret.status == true) {
				layer.closeAll();
				getWeb(1);
				layer.msg('Situs berhasil dibuat', { icon: 1 })
			} else {
				layer.msg(ret.msg, { icon: 2 });
			}
			layer.close(loadT);
		}, 'json');
		return;
	}

	$.post('/site/get_php_version', function (rdata) {

		var defaultPath = $("#defaultPath").html();
		var php_version = "<div class='line'><span class='tname'>" + lan.site.php_ver + "</span><select class='bt-input-text' name='version' id='c_k3' style='width:100px'>";
		for (var i = rdata.length - 1; i >= 0; i--) {
			php_version += "<option value='" + rdata[i].version + "'>" + rdata[i].name + "</option>";
		}

		var www = syncPost('/site/get_root_dir');

		php_version += "</select><span id='php_w' style='color:red;margin-left: 10px;'></span></div>";
		var index = layer.open({
			type: 1,
			area: '600px',
			title: 'Tambah situs',
			content: "<form class='bt-form pd20 pb70' id='addweb'>\
						<div class='line'>\
		                    <span class='tname'>"+ lan.site.domain + "</span>\
		                    <div class='info-r c4'>\
								<textarea id='mainDomain' class='bt-input-text' name='webname' style='width:458px;height:100px;line-height:22px' /></textarea>\
							</div>\
						</div>\
	                    <div class='line'>\
	                    <span class='tname'>Keterangan</span>\
	                    <div class='info-r c4'>\
	                    	<input id='Wbeizhu' class='bt-input-text' type='text' name='ps' placeholder='Keterangan Situs' style='width:458px' />\
	                    </div>\
	                    </div>\
	                    <div class='line'>\
	                    <span class='tname'>Direktori root</span>\
	                    <div class='info-r c4'>\
	                    	<input id='inputPath' class='bt-input-text mr5' type='text' name='path' value='"+ www['dir'] + "/' placeholder='" + www['dir'] + "' style='width:458px' />\
	                    	<span class='glyphicon glyphicon-folder-open cursor' onclick='changePath(\"inputPath\")'></span>\
	                    </div>\
	                    </div>\
						"+ php_version + "\
		                    <div class='bt-form-submit-btn'>\
							<button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>Batal</button>\
							<button type='button' class='btn btn-success btn-sm btn-title' onclick=\"webAdd(1)\">Tambah</button>\
						</div>\
	                  </form>",
		});

		$(function () {
			var placeholder = "<div class='placeholder c9' style='top:10px;left:10px'>" + lan.site.domain_help + "</div>";
			$('#mainDomain').after(placeholder);
			$(".placeholder").click(function () {
				$(this).hide();
				$('#mainDomain').focus();
			})
			$('#mainDomain').focus(function () {
				$(".placeholder").hide();
			});

			$('#mainDomain').blur(function () {
				if ($(this).val().length == 0) {
					$(".placeholder").show();
				}
			});

			$("select[name='version']").change(function () {
				$('#php_w').text('');
			})

			$('#mainDomain').on('input', function () {
				var array;
				var res, ress;
				var str = $(this).val().replace('http://', '').replace('https://', '');
				var len = str.replace(/[^\x00-\xff]/g, "**").length;
				array = str.split("\n");
				ress = array[0].split(":")[0];
				res = ress.replace(new RegExp(/([-.])/g), '_');
				if (res.length > 15) {
					res = res.substr(0, 15);
				}

				var placeholder = $("#inputPath").attr('placeholder');
				$("#inputPath").val(placeholder + '/' + ress);

				if (res.length > 15) {
					res = res.substr(0, 15);
				}

				$("#Wbeizhu").val(ress);
			})

			$('#Wbeizhu').on('input', function () {
				var str = $(this).val();
				var len = str.replace(/[^\x00-\xff]/g, "**").length;
				if (len > 20) {
					str = str.substring(0, 20);
					$(this).val(str);
					layer.msg('Tidak boleh melebihi 20 karakter!', {
						icon: 0
					});
				}
			})
			var timestamp = new Date().getTime().toString();
			var dtpw = timestamp.substring(7);
		});
	}, 'json');
}

function webPathEdit(id) {
	$.post('/site/get_dir_user_ini', '&id=' + id, function (data) {
		var userini = data['data'];
		var webpath = userini['path'];
		var siteName = userini['name'];
		var runPath = userini['runPath']['runPath'];
		var userinicheckeds = userini.userini ? 'checked' : '';
		var logscheckeds = userini.logs ? 'checked' : '';
		var opt = ''
		var selected = '';
		for (var i = 0; i < userini.runPath.dirs.length; i++) {
			selected = '';
			if (userini.runPath.dirs[i] == userini.runPath.runPath) {
				selected = 'selected';
			}
			opt += '<option value="' + userini.runPath.dirs[i] + '" ' + selected + '>' + userini.runPath.dirs[i] + '</option>'
		}
		var webPathHtml = "<div class='webedit-box soft-man-con'>\
					<div class='label-input-group ptb10'>\
						<input type='checkbox' name='userini' id='userini'"+ userinicheckeds + " /><label class='mr20' for='userini' style='font-weight:normal'>Serangan anti-lintas-situs (open_basedir)</label>\
						<input type='checkbox' name='logs' id='logs'"+ logscheckeds + " /><label for='logs' style='font-weight:normal'>Tulis log akses</label>\
					</div>\
					<div class='line mt10'>\
						<span class='mr5'>Direktori situs</span>\
						<input class='bt-input-text mr5' type='text' style='width:50%' placeholder='Direktori root situs' value='"+ webpath + "' name='webdir' id='inputPath'>\
						<span onclick='changePath(&quot;inputPath&quot;)' class='glyphicon glyphicon-folder-open cursor mr20'></span>\
						<button class='btn btn-success btn-sm' onclick='setSitePath("+ id + ")'>Simpan</button>\
					</div>\
					<div class='line mtb15'>\
						<span class='mr5'>Direktori jalankan</span>\
						<select class='bt-input-text' type='text' style='width:50%; margin-right:41px' name='runPath' id='runPath'>"+ opt + "</select>\
						<button class='btn btn-success btn-sm' onclick='setSiteRunPath("+ id + ")' style='margin-top: -1px;'>Simpan</button>\
					</div>\
					<ul class='help-info-text c7 ptb10'>\
						<li>Beberapa program perlu menentukan direktori sekunder sebagai direktori jalankan, seperti Laravel</li>\
						<li>Pilih direktori jalankan Anda, klik simpan</li>\
					</ul>"
			+ '<div class="user_pw_tit" style="margin-top: -8px;padding-top: 11px;">'
			+ '<span class="tit">Akses kata sandi</span>'
			+ '<span class="btswitch-p"><input ' + (userini.pass ? 'checked' : '') + ' class="btswitch btswitch-ios" id="pathSafe" type="checkbox">'
			+ '<label class="btswitch-btn phpmyadmin-btn" for="pathSafe" onclick="pathSafe(' + id + ')"></label>'
			+ '</span>'
			+ '</div>'
			+ '<div class="user_pw" style="margin-top: 10px;display:' + (userini.pass ? 'block;' : 'none;') + '">'
			+ '<p><span>Akun resmi</span><input id="username_get" class="bt-input-text" name="username_get" value="" type="text" placeholder="Jangan diubah, biarkan kosong"></p>'
			+ '<p><span>Kata sandi</span><input id="password_get_1" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="Jangan diubah, biarkan kosong"></p>'
			+ '<p><span>Ulangi Kata sandi</span><input id="password_get_2" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="Jangan diubah, biarkan kosong"></p>'
			+ '<p><button class="btn btn-success btn-sm" onclick="setPathSafe(' + id + ')">Simpan</button></p>'
			+ '</div>'
			+ '</div>';

		$("#webedit-con").html(webPathHtml);
		$("#userini").change(function () {
			$.post('/site/set_dir_user_ini', {
				'path': webpath,
				'runPath': runPath,
			}, function (userini) {
				layer.msg(userini.msg + '<p style="color:red;">Note: Setting anti-cross-site needs to restart PHP to take effect!</p>', { icon: userini.status ? 1 : 2 });
				tryRestartPHP(siteName);
			}, 'json');
		});

		$("#logs").change(function () {
			var loadT = layer.msg("Setting up...", { icon: 16, time: 10000, shade: [0.3, '#000'] });
			$.post('/site/logs_open', 'id=' + id, function (rdata) {
				layer.close(loadT);
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			}, 'json');
		});

	}, 'json');
}

function pathSafe(id) {
	var isPass = $('#pathSafe').prop('checked');
	if (!isPass) {
		$(".user_pw").show();
	} else {
		var loadT = layer.msg(lan.public.the, { icon: 16, time: 10000, shade: [0.3, '#000'] });
		$.post('/site/close_has_pwd', { id: id }, function (rdata) {
			layer.close(loadT);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			$(".user_pw").hide();
		}, 'json');
	}
}

function setPathSafe(id) {
	var username = $("#username_get").val();
	var pass1 = $("#password_get_1").val();
	var pass2 = $("#password_get_2").val();
	if (pass1 != pass2) {
		layer.msg('Kedua kata sandi yang dimasukkan tidak cocok!', { icon: 2 });
		return;
	}
	var loadT = layer.msg('Sedang memproses, mohon tunggu...', { icon: 16, time: 10000, shade: [0.3, '#000'] });
	$.post('/site/set_has_pwd', { id: id, username: username, password: pass1 }, function (rdata) {
		layer.close(loadT);
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function setSiteRunPath(id) {
	var NewPath = $("#runPath").val();
	var loadT = layer.msg(lan.public.the, { icon: 16, time: 10000, shade: [0.3, '#000'] });
	$.post('/site/set_site_run_path', 'id=' + id + '&runPath=' + NewPath, function (rdata) {
		layer.close(loadT);
		var ico = rdata.status ? 1 : 2;
		layer.msg(rdata.msg, { icon: ico });
	}, 'json');
}

function setSitePath(id) {
	var NewPath = $("#inputPath").val();
	var loadT = layer.msg('Sedang memproses, mohon tunggu...', { icon: 16, time: 10000, shade: [0.3, '#000'] });
	$.post('/site/set_path', 'id=' + id + '&path=' + NewPath, function (rdata) {
		layer.close(loadT);
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function webBakEdit(id) {
	$.post("/data?action=getKey','table=sites&key=ps&id=" + id, function (rdata) {
		var webBakHtml = "<div class='webEdit-box padding-10'>\
					<div class='line'>\
					<label><span>"+ lan.site.note_ph + "</span></label>\
					<div class='info-r'>\
					<textarea name='beizhu' id='webbeizhu' col='5' style='width:96%'>"+ rdata + "</textarea>\
					<br><br><button class='btn btn-success btn-sm' onclick='SetSitePs("+ id + ")'>Simpan</button>\
					</div>\
					</div>";
		$("#webedit-con").html(webBakHtml);
	});
}

function setIndexEdit(id) {
	$.post('/site/get_index', 'id=' + id, function (data) {
		var rdata = data['index'];
		rdata = rdata.replace(new RegExp(/(,)/g), "\n");
		var setIndexHtml = "<div id='SetIndex'><div class='SetIndex'>\
				<div class='line'>\
						<textarea class='bt-input-text' id='Dindex' name='files' style='height: 180px; width:50%; line-height:20px'>"+ rdata + "</textarea>\
						<button type='button' class='btn btn-success btn-sm pull-right' onclick='setIndexList("+ id + ")' style='margin: 70px 130px 0px 0px;'>" + lan.public.save + "</button>\
				</div>\
				<ul class='help-info-text c7 ptb10'>\
					<li>Dokumen default, satu per baris, dengan prioritas dari atas ke bawah.</li>\
				</ul>\
				</div></div>";
		$("#webedit-con").html(setIndexHtml);
	}, 'json');
}

function webStop(wid, wname) {
	layer.confirm('Setelah situs dinonaktifkan, Anda tidak akan dapat mengaksesnya. Apakah Anda yakin ingin menonaktifkan situs ini？', { icon: 3, closeBtn: 2 }, function (index) {
		if (index > 0) {
			var loadT = layer.load();
			$.post("/site/stop", "id=" + wid + "&name=" + wname, function (ret) {
				layer.msg(ret.msg, { icon: ret.status ? 1 : 2 })
				layer.close(loadT);
				getWeb(1);
			}, 'json');
		}
	});
}

function webStart(wid, wname) {
	layer.confirm('Akan meluncurkan situs, apakah Anda yakin ingin meluncurkan situs ini?', { icon: 3, closeBtn: 2 }, function (index) {
		if (index > 0) {
			var loadT = layer.load()
			$.post("/site/start", "id=" + wid + "&name=" + wname, function (ret) {
				layer.msg(ret.msg, { icon: ret.status ? 1 : 2 })
				layer.close(loadT);
				getWeb(1);
			}, 'json');
		}
	});
}

function webDelete(wid, wname) {
	var thtml = "<div class='options'>\
	    	<label><input type='checkbox' id='delpath' name='path'><span>Direktori root</span></label>\
	    	</div>";
	var info = 'Apakah Anda ingin menghapus direktori root dengan nama yang sama?';
	safeMessage('Hapus situs ' + "[" + wname + "]", info, function () {
		var path = '';
		if ($("#delpath").is(":checked")) {
			path = '&path=1';
		}
		var loadT = layer.msg('Sedang memproses, mohon tunggu...', { icon: 16, time: 10000, shade: [0.3, '#000'] });
		$.post("/site/delete", "id=" + wid + "&webname=" + wname + path, function (ret) {
			layer.closeAll();
			layer.msg(ret.msg, { icon: ret.status ? 1 : 2 })
			getWeb(1);
		}, 'json');
	}, thtml);
}

function allDeleteSite() {
	var checkList = $("input[name=id]");
	var dataList = new Array();
	for (var i = 0; i < checkList.length; i++) {
		if (!checkList[i].checked) continue;
		var tmp = new Object();
		tmp.name = checkList[i].title;
		tmp.id = checkList[i].value;
		dataList.push(tmp);
	}

	var thtml = "<div class='options'>\
	    	<label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>"+ lan.site.all_del_info + "</span></label>\
	    	</div>";
	safeMessage(lan.site.all_del_site, "<a style='color:red;'>" + lan.get('del_all_site', [dataList.length]) + "</a>", function () {
		layer.closeAll();
		var path = '';
		if ($("#delpath").is(":checked")) {
			path = '&path=1';
		}
		syncDeleteSite(dataList, 0, '', path);
	}, thtml);
}

function syncDeleteSite(dataList, successCount, errorMsg, path) {
	if (dataList.length < 1) {
		layer.msg(lan.get('del_all_site_ok', [successCount]), { icon: 1 });
		return;
	}
	var loadT = layer.msg(lan.get('del_all_task_the', [dataList[0].name]), { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.ajax({
		type: 'POST',
		url: '/site?action=DeleteSite',
		data: 'id=' + dataList[0].id + '&webname=' + dataList[0].name + path,
		async: true,
		success: function (frdata) {
			layer.close(loadT);
			if (frdata.status) {
				successCount++;
				$("input[title='" + dataList[0].name + "']").parents("tr").remove();
			} else {
				if (!errorMsg) {
					errorMsg = '<br><p>' + lan.site.del_err + ':</p>';
				}
				errorMsg += '<li>' + dataList[0].name + ' -> ' + frdata.msg + '</li>'
			}

			dataList.splice(0, 1);
			syncDeleteSite(dataList, successCount, errorMsg, path);
		}
	});
}

function domainEdit(id, name, msg, status) {
	$.post('/site/get_domain', { pid: id }, function (domain) {

		var echoHtml = "";
		for (var i = 0; i < domain.length; i++) {
			echoHtml += "<tr>\
				<td><a title='"+ lan.site.click_access + "' target='_blank' href='http://" + domain[i].name + ":" + domain[i].port + "' class='btlinkbed'>" + domain[i].name + "</a></td>\
				<td><a class='btlinkbed'>" + domain[i].port + "</a></td>\
				<td class='text-center'><a class='table-btn-del' href='javascript:;' onclick=\"delDomain(" + id + ",'" + name + "','" + domain[i].name + "','" + domain[i].port + "',1)\"><span class='glyphicon glyphicon-trash'></span></a></td>\
				</tr>";
		}
		var bodyHtml = "<textarea id='newdomain' class='bt-input-text' style='height: 100px; width: 340px;padding:5px 10px;line-height:20px'></textarea>\
								<input type='hidden' id='newport' value='80' />\
								<button type='button' class='btn btn-success btn-sm pull-right' style='margin:30px 35px 0 0' onclick=\"domainAdd(" + id + ",'" + name + "',1)\">Add to</button>\
							<div class='divtable mtb15' style='height:350px;overflow:auto'>\
								<table class='table table-hover' width='100%'>\
								<thead><tr><th>"+ lan.site.domain + "</th><th width='70px'>Port</th><th width='50px' class='text-center'>Action</th></tr></thead>\
								<tbody id='checkDomain'>" + echoHtml + "</tbody>\
								</table>\
							</div>";
		$("#webedit-con").html(bodyHtml);
		if (msg != undefined) {
			layer.msg(msg, { icon: status ? 1 : 5 });
		}
		var placeholder = "<div class='placeholder c9' style='left:28px;width:330px;top:16px;'>Isi nama domain di setiap baris, defaultnya adalah port 80<br>Metode analisis pan untuk menambahkan *.domain.com<br>Jika Anda menambahkan port lain, formatnya adalah www.domain.com:88</div>";
		$('#newdomain').after(placeholder);
		$(".placeholder").click(function () {
			$(this).hide();
			$('#newdomain').focus();
		})
		$('#newdomain').focus(function () {
			$(".placeholder").hide();
		});

		$('#newdomain').blur(function () {
			if ($(this).val().length == 0) {
				$(".placeholder").show();
			}
		});
		$("#newdomain").on("input", function () {
			var str = $(this).val();
			if (isChineseChar(str)) {
				$('.btn-zhm').show();
			} else {
				$('.btn-zhm').hide();
			}
		})
		//checkDomain();
	}, 'json');
}

function cancelSend() {
	$(".changeDomain,.changePort").hide().prev().show();
	$(".changeDomain,.changePort").remove();
}

function checkDomain() {
	$("#checkDomain tr").each(function () {
		var $this = $(this);
		var domain = $(this).find("td:first-child").text();
		$(this).find("td:first-child").append("<i class='lading'></i>");
	});
}

function domainAdd(id, webname, type) {
	var Domain = $("#newdomain").val().split("\n");

	var domainlist = '';
	for (var i = 0; i < Domain.length; i++) {
		domainlist += Domain[i] + ',';
	}

	if (domainlist.length < 3) {
		layer.msg(lan.site.domain_empty, { icon: 5 });
		return;
	}

	domainlist = domainlist.substring(0, domainlist.length - 1);
	var loadT = layer.load();
	var data = "domain=" + domainlist + "&webname=" + webname + "&id=" + id;
	$.post('/site/add_domain', data, function (retuls) {
		layer.close(loadT);
		domainEdit(id, webname, retuls.msg, retuls.status);
	}, 'json');
}

function delDomain(wid, wname, domain, port, type) {
	var num = $("#checkDomain").find("tr").length;
	if (num == 1) {
		layer.msg(lan.site.domain_last_cannot);
	}
	layer.confirm(lan.site.domain_del_confirm, { icon: 3, closeBtn: 2 }, function (index) {
		var url = "/site/del_domain"
		var data = "id=" + wid + "&webname=" + wname + "&domain=" + domain + "&port=" + port;
		var loadT = layer.msg(lan.public.the_del, { time: 0, icon: 16 });
		$.post(url, data, function (ret) {
			layer.close(loadT);
			layer.msg(ret.msg, { icon: ret.status ? 1 : 2 })
			if (type == 1) {
				layer.close(loadT);
				domainEdit(wid, wname)
			} else {
				layer.closeAll();
				DomainRoot(wid, wname);
			}
		}, 'json');
	});
}

function isDomain(domain) {
	//domain = 'http://'+domain;
	var re = new RegExp();
	re.compile("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_%&\?\/.=]+$");
	if (re.test(domain)) {
		return (true);
	} else {
		return (false);
	}
}

function webBackup(id, name) {
	var loadT = layer.msg('Backup in progress, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/to_backup', "id=" + id, function (rdata) {
		layer.closeAll();
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });

		getBackup(id);
	}, 'json');
}

function webBackupDelete(id, pid) {
	layer.confirm('Apakah Anda yakin ingin menghapus paket cadangan?', { title: 'Hapus file cadangan!', icon: 3, closeBtn: 2 }, function (index) {
		var loadT = layer.msg('Sedang menghapus, mohon tunggu...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/site/del_backup', 'id=' + id, function (rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			getBackup(pid);
		}, 'json');
	})
}

function getBackup(id, name, page) {

	if (typeof (page) == 'undefined') {
		page = '1';
	}
	$.post('/site/get_backup', 'search=' + id + '&limit=5&p=' + page, function (frdata) {
		var body = '';
		for (var i = 0; i < frdata.data.length; i++) {
			if (frdata.data[i].type == '1') {
				continue;
			}

			var ftpdown = "<a class='btlink' href='/files/download?filename=" + frdata.data[i].filename + "&name=" + frdata.data[i].name + "' target='_blank'>Unduh</a> | ";
			body += "<tr><td><span class='glyphicon glyphicon-file'></span>" + frdata.data[i].name + "</td>\
					<td>" + (toSize(frdata.data[i].size)) + "</td>\
					<td>" + frdata.data[i].addtime + "</td>\
					<td class='text-right' style='color:#ccc'>"+ ftpdown + "<a class='btlink' href='javascript:;' onclick=\"webBackupDelete('" + frdata.data[i].id + "'," + id + ")\">Hapus</a></td>\
				</tr>"
		}

		var ftpdown = '';
		frdata.page = frdata.page.replace(/'/g, '"').replace(/getBackup\(/g, "getBackup(" + id + ",0,");

		if (name == 0) {
			var sBody = "<table width='100%' id='webBackupList' class='table table-hover'>\
						<thead><tr><th>Nama file</th><th>Ukuran</th><th>Diubah</th><th width='140px' class='text-right'>Aksi< /th></tr></thead>\
						<tbody id='webBackupBody' class='list-list'>"+ body + "</tbody>\
						</table>"
			$("#webBackupList").html(sBody);
			$(".page").html(frdata.page);
			return;
		}
		layer.closeAll();
		layer.open({
			type: 1,
			skin: 'demo-class',
			area: '700px',
			title: 'Paket cadangan',
			closeBtn: 1,
			shift: 0,
			shadeClose: false,
			content: "<div class='bt-form ptb15 mlr15' id='webBackup'>\
						<button class='btn btn-default btn-sm' style='margin-right:10px' type='button' onclick=\"webBackup('" + frdata['site']['id'] + "','" + frdata['site']['name'] + "')\">Paket cadangan</button>\
						<div class='divtable mtb15' style='margin-bottom:0'>\
							<table width='100%' id='webBackupList' class='table table-hover'>\
							<thead>\
								<tr><th>Nama file</th><th>Ukuran</th><th>Diubah</th><th width='140px' class='text-right'>Aksi</th> </tr>\
							</thead>\
							<tbody id='webBackupBody' class='list-list'>" + body + "</tbody>\
							</table>\
							<div class='page'>" + frdata.page + "</div>\
						</div>\
					</div>"
		});
	}, 'json');
}

function goSet(num) {
	var el = document.getElementsByTagName('input');
	var len = el.length;
	var data = '';
	var a = '';
	var count = 0;

	for (var i = 0; i < len; i++) {
		if (el[i].checked == true && el[i].value != 'on') {
			data += a + count + '=' + el[i].value;
			a = '&';
			count++;
		}
	}

	if (num == 1) {
		reAdd(data);
	}
	else if (num == 2) {
		shift(data);
	}
}

function setIndex(id) {
	var quanju = (id == undefined) ? lan.site.public_set : lan.site.local_site;
	var data = id == undefined ? "" : "id=" + id;
	$.post('/site?action=GetIndex', data, function (rdata) {
		rdata = rdata.replace(new RegExp(/(,)/g), "\n");
		layer.open({
			type: 1,
			area: '500px',
			title: lan.site.setindex,
			closeBtn: 1,
			shift: 5,
			shadeClose: true,
			content: "<form class='bt-form' id='SetIndex'><div class='SetIndex'>"
				+ "<div class='line'>"
				+ "	<span class='tname' style='padding-right:2px'>" + lan.site.default_doc + "</span>"
				+ "	<div class='info-r'>"
				+ "		<textarea id='Dindex' name='files' style='line-height:20px'>" + rdata + "</textarea>"
				+ "		<p>" + quanju + lan.site.default_doc_help + "</p>"
				+ "	</div>"
				+ "</div>"
				+ "<div class='bt-form-submit-btn'>"
				+ "	<button type='button' id='web_end_time' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>" + lan.public.cancel + "</button>"
				+ "    <button type='button' class='btn btn-success btn-sm btn-title' onclick='setIndexList(" + id + ")'>" + lan.public.ok + "</button>"
				+ "</div>"
				+ "</div></form>"
		});
	});
}

function setDefaultSite() {
	var name = $("#default_site").val();
	var loadT = layer.msg('Lagi diproses, tunggu bentar...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/set_default_site', 'name=' + name, function (rdata) {
		layer.closeAll();
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
	}, 'json');
}

function getDefaultSite() {
	$.post('/site/get_default_site', '', function (rdata) {
		var opt = '<option value="off">Situs default belum diatur</option>';
		var selected = '';
		for (var i = 0; i < rdata.sites.length; i++) {
			selected = '';
			if (rdata.default_site == rdata.sites[i].name) selected = 'selected';
			opt += '<option value="' + rdata.sites[i].name + '" ' + selected + '>' + rdata.sites[i].name + '</option>';
		}

		layer.open({
			type: 1,
			area: '530px',
			title: 'Atur situs default',
			closeBtn: 1,
			shift: 5,
			shadeClose: true,
			content: '<div class="bt-form ptb15 pb70">\
						<p class="line">\
							<span class="tname text-right">Situs default</span>\
							<select id="default_site" class="bt-input-text" style="width: 300px;">'+ opt + '</select>\
						</p>\
						<ul class="help-info-text c6 plr20">\
						    <li>Setelah situs default diatur, semua domain dan IP yang nggak terikat bakal diarahkan ke situs default ini</li>\
						    <li>Bisa efektif mencegah analisis berbahaya</li>\
					    </ul>\
						<div class="bt-form-submit-btn">\
							<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">Batal</button>\
							<button class="btn btn-success btn-sm btn-title" onclick="setDefaultSite()">Kirim</button>\
						</div>\
					</div>'
		});
	}, 'json');
}

function setPHPVer() {
	$.post('/site/get_cli_php_version', '', function (rdata) {
		if (typeof (rdata['status']) != 'undefined') {
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			return;
		}

		var opt = '';
		var selected = '';
		for (var i = 0; i < rdata.versions.length; i++) {
			selected = '';
			if (rdata.select.version == rdata.versions[i].version) selected = 'selected';

			if (rdata.versions[i].version.indexOf("yum") > -1) {
				continue;
			}

			if (rdata.versions[i].version.indexOf("apt") > -1) {
				continue;
			}

			opt += '<option value="' + rdata.versions[i].version + '" ' + selected + '>' + rdata.versions[i].name + '</option>';
		}

		var phpver_layer = layer.open({
			type: 1,
			area: '530px',
			title: 'Atur versi PHP-CLI (baris perintah)',
			closeBtn: 1,
			shift: 5,
			shadeClose: true,
			btn: ["Ya", "Tidak"],
			content: '<div class="bt-form ptb15">\
						<p class="line">\
							<span class="tname text-right">Versi PHP-CLI</span>\
							<select id="default_ver" class="bt-input-text" style="width: 300px;">'+ opt + '</select>\
						</p>\
						<ul class="help-info-text c6 plr20">\
						    <li>Di sini kamu bisa atur versi PHP yang dipakai pas jalanin php di baris perintah</li>\
						    <li>Ini perlu diatur ulang setelah instal versi PHP baru</li>\
					    </ul>\
					</div>',
			yes: function (layero, index) {
				var version = $("#default_ver").val();
				var loadT = layer.msg('Lagi diproses, tunggu bentar...', { icon: 16, time: 0, shade: [0.3, '#000'] });
				$.post('/site/set_cli_php_version', 'version=' + version, function (rdata) {
					layer.close(loadT);
					showMsg(rdata.msg, function () {
						if (rdata.status) {
							layer.close(phpver_layer);
						}
					}, { icon: rdata.status ? 1 : 5 }, 2000);
				}, 'json');
			},
		});
	}, 'json');
}

function setIndexList(id) {
	var Dindex = $("#Dindex").val().replace(new RegExp(/(\n)/g), ",");
	if (id == undefined) {
		var data = "id=&index=" + Dindex;
	} else {
		var data = "id=" + id + "&index=" + Dindex;
	}
	var loadT = layer.load(2);
	$.post('/site/set_index', data, function (rdata) {
		layer.close(loadT);
		var ico = rdata.status ? 1 : 5;
		layer.msg(rdata.msg, { icon: ico });
	}, 'json');
}

function webEdit(id, website, endTime, addtime) {
	layer.open({
		type: 1,
		area: '700px',
		title: 'Ubah situs [' + website + ']  --  Waktu tambah [' + addtime + ']',
		closeBtn: 1,
		shift: 0,
		content: "<div class='bt-form'>\
			<div class='bt-w-menu pull-left' style='height: 565px;'>\
				<p class='bgw'  onclick=\"domainEdit(" + id + ",'" + website + "')\">Manajemen Domain</p>\
				<p onclick='dirBinding("+ id + ")' title='Binding Subdirektori'>Binding Folder</p>\
				<p onclick='webPathEdit("+ id + ")' title='Direktori website'>Direktori website</p>\
				<p onclick='limitNet("+ id + ")' title='Batasan trafik'>Batasan trafik</p>\
				<p onclick=\"rewrite('"+ website + "')\" title='Rewrite'>Rewrite</p>\
				<p onclick='setIndexEdit("+ id + ")' title='Dokumen default'>Index Default</p>\
				<p onclick=\"configFile('"+ website + "')\" title='File konfigurasi'>Konfig</p>\
				<p onclick=\"setSSL("+ id + ",'" + website + "')\" title='SSL'>SSL</p>\
				<p onclick=\"phpVersion('"+ website + "')\" title='Versi PHP'>Versi PHP</p>\
				<p onclick=\"to301('"+ website + "')\" title='Redirect'>Redirect</p>\
				<p onclick=\"toProxy('"+ website + "')\" title='Proxy'>Proxy</p>\
				<p id='site_"+ id + "' onclick=\"security('" + id + "','" + website + "')\" title='Anti-leech'>Anti-leech</p>\
				<p id='site_"+ id + "' onclick=\"getSiteLogs('" + website + "')\" title='Lihat log akses situs'>Log Akses</p>\
				<p id='site_"+ id + "' onclick=\"getSiteErrorLogs('" + website + "')\" title='Lihat log error situs'>Log Error</p>\
			</div>\
			<div id='webedit-con' class='bt-w-con webedit-con pd15' style='height: 565px;overflow: scroll;'></div>\
		</div>",
		success: function () {
			var placeholder = "<div class='placeholder'>Isi satu nama domain tiap baris, defaultnya port 80<br>Bisa pakai *.domain.com buat analisis pan<br>Kalau mau tambah port lain, formatnya www.domain.com:88</div>";
			$('#newdomain').after(placeholder);
			$(".placeholder").click(function () {
				$(this).hide();
				$('#newdomain').focus();
			});

			$('#newdomain').focus(function () {
				$(".placeholder").hide();
			});

			$('#newdomain').blur(function () {
				if ($(this).val().length == 0) {
					$(".placeholder").show();
				}
			});

			$(".bt-w-menu p").click(function () {
				$(this).addClass("bgw").siblings().removeClass("bgw");
			});

			domainEdit(id, website);
		}
	});
}

function getSiteLogs(siteName) {
	var loadT = layer.msg('Lagi diproses, tunggu bentar...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/get_logs', { siteName: siteName }, function (logs) {
		layer.close(loadT);
		if (logs.status !== true) {
			logs.msg = '';
		}
		if (logs.msg == '') logs.msg = 'Lagi nggak ada log.';
		var phpCon = '<textarea wrap="off" readonly="" style="white-space: pre;margin: 0px;width: 560px;height: 530px;background-color: #333;color:#fff; padding:0 5px" id="error_log">' + logs.msg + '</textarea>';
		$("#webedit-con").html(phpCon);
		var ob = document.getElementById('error_log');
		ob.scrollTop = ob.scrollHeight;
	}, 'json');
}

function getSiteErrorLogs(siteName) {
	var loadT = layer.msg('Processing, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/get_error_logs', { siteName: siteName }, function (logs) {
		// console.log(logs);
		layer.close(loadT);
		if (logs.status !== true) {
			logs.msg = '';
		}
		if (logs.msg == '') logs.msg = 'Currently no logs.';
		var phpCon = '<textarea wrap="off" readonly="" style="white-space: pre;margin: 0px;width: 560px;height: 530px;background-color: #333;color:#fff; padding:0 5px" id="error_log">' + logs.msg + '</textarea>';
		$("#webedit-con").html(phpCon);
		var ob = document.getElementById('error_log');
		ob.scrollTop = ob.scrollHeight;
	}, 'json');
}

function security(id, name) {
	var loadT = layer.msg(lan.site.the_msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/get_security', { id: id, name: name }, function (rdata) {
		layer.close(loadT);
		var mbody = '<div>'
			+ '<p style="margin-bottom:8px"><span style="display: inline-block; width: 60px;">Akhiran URL</span><input class="bt-input-text" type="text" name="sec_fix" value="' + rdata.fix + '" style="margin-left: 5px;width: 425px;height: 30px;margin-right:10px;' + (rdata.status ? 'background-color: #eee;' : '') + '" placeholder="Kalau banyak pisahin pakai koma, misal: png,jpeg,jpg,gif,zip" ' + (rdata.status ? 'readonly' : '') + '></p>'
			+ '<p style="margin-bottom:8px"><span style="display: inline-block; width: 60px;">Nama domain</span><input class="bt-input-text" type="text" name="sec_domains" value="' + rdata.domains + '" style="margin-left: 5px;width: 425px;height: 30px;margin-right:10px;' + (rdata.status ? 'background-color: #eee;' : '') + '" placeholder="Bisa pakai wildcard, pisahin beberapa domain pakai koma, misal: *.example.com, example.com" ' + (rdata.status ? 'readonly' : '') + '></p>'
			+ '<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="sec_status" onclick="setSecurity(\'' + name + '\',' + id + ')" ' + (rdata.status ? 'checked' : '') + '>Nyalain anti-leech</label></div>'
			+ '<ul class="help-info-text c7 ptb10">'
			+ '<li>Defaultnya sumber daya boleh diakses langsung, maksudnya request dengan HTTP_REFERER kosong nggak dibatasi</li>'
			+ '<li>Akhiran URL dan nama domain yang banyak harus dipisahin pakai koma (,), misal: png,jpeg,zip,js</li>'
			+ '<li>Pas anti-leech aktif, sistem bakal langsung balikin status 404</li>'
			+ '</ul>'
			+ '</div>'
		$("#webedit-con").html(mbody);
	}, 'json');
}

function setSecurity(name, id) {
	var data = {
		fix: $("input[name='sec_fix']").val(),
		domains: $("input[name='sec_domains']").val(),
		status: $("input[name='sec_status']").val(),
		name: name,
		id: id
	}
	var loadT = layer.msg(lan.site.the_msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/set_security', data, function (rdata) {
		layer.close(loadT);
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		if (rdata.status) setTimeout(function () { security(id, name); }, 1000);
	}, 'json');
}

function limitNet(id) {
	$.post('/site/get_limit_net', 'id=' + id, function (rdata) {
		var status_selected = rdata.perserver != 0 ? 'checked' : '';
		if (rdata.perserver == 0) {
			rdata.perserver = 300;
			rdata.perip = 25;
			rdata.limit_rate = 512;
		}
		var limitList = "<option value='1' " + ((rdata.perserver == 0 || rdata.perserver == 300) ? 'selected' : '') + ">" + lan.site.limit_net_1 + "</option>"
			+ "<option value='2' " + ((rdata.perserver == 200) ? 'selected' : '') + ">" + lan.site.limit_net_2 + "</option>"
			+ "<option value='3' " + ((rdata.perserver == 50) ? 'selected' : '') + ">" + lan.site.limit_net_3 + "</option>"
			+ "<option value='4' " + ((rdata.perserver == 500) ? 'selected' : '') + ">" + lan.site.limit_net_4 + "</option>"
			+ "<option value='5'  " + ((rdata.perserver == 400) ? 'selected' : '') + ">" + lan.site.limit_net_5 + "</option>"
			+ "<option value='6' " + ((rdata.perserver == 60) ? 'selected' : '') + ">" + lan.site.limit_net_6 + "</option>"
			+ "<option value='7' " + ((rdata.perserver == 150) ? 'selected' : '') + ">" + lan.site.limit_net_7 + "</option>"
		var body = "<div class='dirBinding flow c4'>"
			+ '<p class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" ' + status_selected + ' onclick="saveLimitNet(' + id + ')" style="width:15px;height:15px;margin-right:5px" />' + lan.site.limit_net_8 + '</label></p>'
			+ "<p class='line' style='padding:10px 0'><span class='span_tit mr5'>" + lan.site.limit_net_9 + "：</span><select class='bt-input-text mr20' name='limit' style='width:90px'>" + limitList + "</select></p>"
			+ "<p class='line' style='padding:10px 0'><span class='span_tit mr5'>" + lan.site.limit_net_10 + "：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='perserver' value='" + rdata.perserver + "' /></p>"
			+ "<p class='line' style='padding:10px 0'><span class='span_tit mr5'>" + lan.site.limit_net_12 + "：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='perip' value='" + rdata.perip + "' /></p>"
			+ "<p class='line' style='padding:10px 0'><span class='span_tit mr5'>" + lan.site.limit_net_14 + "：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='limit_rate' value='" + rdata.limit_rate + "' /></p>"
			+ "<button class='btn btn-success btn-sm mt10' onclick='saveLimitNet(" + id + ",1)'>" + lan.public.save + "</button>"
			+ "</div>"
			+ "<ul class='help-info-text c7 mtb15'><li>" + lan.site.limit_net_11 + "</li><li>" + lan.site.limit_net_13 + "</li><li>" + lan.site.limit_net_15 + "</li></ul>"
		$("#webedit-con").html(body);

		$("select[name='limit']").change(function () {
			var type = $(this).val();
			perserver = 300;
			perip = 25;
			limit_rate = 512;
			switch (type) {
				case '1':
					perserver = 300;
					perip = 25;
					limit_rate = 512;
					break;
				case '2':
					perserver = 200;
					perip = 10;
					limit_rate = 1024;
					break;
				case '3':
					perserver = 50;
					perip = 3;
					limit_rate = 2048;
					break;
				case '4':
					perserver = 500;
					perip = 10;
					limit_rate = 2048;
					break;
				case '5':
					perserver = 400;
					perip = 15;
					limit_rate = 1024;
					break;
				case '6':
					perserver = 60;
					perip = 10;
					limit_rate = 512;
					break;
				case '7':
					perserver = 150;
					perip = 4;
					limit_rate = 1024;
					break;
			}

			$("input[name='perserver']").val(perserver);
			$("input[name='perip']").val(perip);
			$("input[name='limit_rate']").val(limit_rate);
		});
	}, 'json');
}

function saveLimitNet(id, type) {
	var isChecked = $("input[name='status']").attr('checked');
	if (isChecked == undefined || type == 1) {
		var data = 'id=' + id + '&perserver=' + $("input[name='perserver']").val() + '&perip=' + $("input[name='perip']").val() + '&limit_rate=' + $("input[name='limit_rate']").val();
		var loadT = layer.msg(lan.public.config, { icon: 16, time: 10000 })
		$.post('/site/save_limit_net', data, function (rdata) {
			layer.close(loadT);
			limitNet(id);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		}, 'json');
	} else {
		var loadT = layer.msg(lan.public.config, { icon: 16, time: 10000 })
		$.post('/site/close_limit_net', { id: id }, function (rdata) {
			layer.close(loadT);
			limitNet(id);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		}, 'json');
	}
}

function dirBinding(id) {
	$.post('/site/get_dir_binding', { 'id': id }, function (data) {
		var rdata = data['data'];
		var echoHtml = '';
		for (var i = 0; i < rdata.binding.length; i++) {
			echoHtml += "<tr><td>" + rdata.binding[i].domain + "</td><td>" + rdata.binding[i].port + "</td><td>" + rdata.binding[i].path + "</td><td class='text-right'><a class='btlink' href='javascript:setDirRewrite(" + rdata.binding[i].id + ");'>Rewrite</a> | <a class='btlink' href='javascript:delDirBind(" + rdata.binding[i].id + "," + id + ");'>Delete</a></td></tr>";
		}

		var dirList = '';
		for (var n = 0; n < rdata.dirs.length; n++) {
			dirList += "<option value='" + rdata.dirs[n] + "'>" + rdata.dirs[n] + "</option>";
		}

		var body = "<div class='dirBinding c5'>"
			+ "Domain：<input class='bt-input-text mr20' type='text' name='domain' />"
			+ "Subfolder：<select class='bt-input-text mr20' name='dirName'>" + dirList + "</select>"
			+ "<button class='btn btn-success btn-sm' onclick='addDirBinding(" + id + ")'>Tambah</button>"
			+ "</div>"
			+ "<div class='divtable mtb15' style='height:470px;overflow:auto'><table class='table table-hover' width='100%' style='margin-bottom:0'>"
			+ "<thead><tr><th>Domain</th><th width='70'>Port</th><th width='100'>Subdirektori</th><th width='100' class='text-right'>Aksi</th></tr></thead>"
			+ "<tbody id='checkDomain'>" + echoHtml + "</tbody>"
			+ "</table></div>";

		$("#webedit-con").html(body);
	}, 'json');
}

function setDirRewrite(id) {
	$.post('/site/get_dir_bind_rewrite', 'id=' + id, function (rdata) {
		if (!rdata.status) {
			var confirmObj = layer.confirm('Yakin mau buat aturan pseudo-static terpisah buat subdirektori ini?', { icon: 3, closeBtn: 2 }, function () {
				$.post('/site/get_dir_bind_rewrite', 'id=' + id + '&add=1', function (rdata) {
					layer.close(confirmObj);
					showRewrite(rdata);
				}, 'json');
			});
			return;
		}
		showRewrite(rdata);
	}, 'json');
}

function showRewrite(rdata) {
	var rList = '';
	for (var i = 0; i < rdata.rlist.length; i++) {
		rList += "<option value='" + rdata.rlist[i] + "'>" + rdata.rlist[i] + "</option>";
	}
	var webBakHtml = "<div class='c5 plr15'>\
				<div class='line'>\
					<select class='bt-input-text mr20' id='myRewrite' name='rewrite' style='width:30%;'>"+ rList + "</select>\
					<textarea class='bt-input-text mtb15' style='height: 260px; width: 470px; line-height:18px;padding:5px;' id='rewriteBody'>"+ rdata.data + "</textarea>\
				</div>\
				<button id='setRewriteBtn' class='btn btn-success btn-sm'>Simpan</button>\
				<ul class='help-info-text c7 ptb10'>\
					<li>Pilih aplikasi kamu. Kalau website nggak bisa diakses normal setelah atur pseudo-static, coba balikin ke default.</li>\
					<li>Kamu bisa ubah aturan pseudo-static, trus simpan kalau udah selesai.</li>\
				</ul>\
			</div>";
	layer.open({
		type: 1,
		area: '500px',
		title: 'Atur aturan rewrite',
		closeBtn: 1,
		shift: 5,
		shadeClose: true,
		content: webBakHtml,
		success: function () {

			$("#myRewrite").change(function () {
				var rewriteName = $(this).val();
				$.post('/files/get_body', 'path=' + rdata['rewrite_dir'] + '/' + rewriteName + '.conf', function (fileBody) {
					$("#rewriteBody").val(fileBody.data.data);
				}, 'json');
			});

			$('#setRewriteBtn').click(function () {
				var data = $("#rewriteBody").val();
				setRewrite(rdata.filename, encodeURIComponent(data));
			});
		}
	});
}

function addDirBinding(id) {
	var domain = $("input[name='domain']").val();
	var dirName = $("select[name='dirName']").val();
	if (domain == '' || dirName == '' || dirName == null) {
		layer.msg(lan.site.d_s_empty, { icon: 2 });
		return;
	}

	var data = 'id=' + id + '&domain=' + domain + '&dirName=' + dirName;
	$.post('/site/add_dir_bind', data, function (rdata) {
		dirBinding(id);
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function delDirBind(id, siteId) {
	layer.confirm(lan.site.s_bin_del, { icon: 3, closeBtn: 2 }, function () {
		$.post('/site/del_dir_bind', 'id=' + id, function (rdata) {
			dirBinding(siteId);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		}, 'json');
	});
}

function to301(siteName, type, obj) {

	if (type == 1) {
		obj = {
			to: 'http://',
			from: '',
			r_type: '',
			type: 1,
			type: 'path',
			keep_path: 1
		}
		var redirect_form = layer.open({
			type: 1,
			skin: 'demo-class',
			area: '650px',
			title: type == 1 ? 'buat pengalihan' : 'ubah pengalihan [' + obj.redirectname + ']',
			closeBtn: 1,
			shift: 5,
			shadeClose: false,
			content: "<form id='form_redirect' class='divtable pd20' style='padding-bottom: 60px'>" +
				"<div class='line' style='overflow:hidden;height: 40px;'>" +
				"<div style='display: inline-block;'>" +
				"<span class='tname' style='margin-left:10px;position: relative;top: -5px;'>Simpan parameter URI</span>" +
				"<input class='btswitch btswitch-ios' id='keep_path' type='checkbox' name='keep_path' " + (obj.keep_path == 1 ? 'checked="checked"' : '') + " /><label class='btswitch-btn phpmyadmin-btn' for='keep_path' style='float:left'></label>" +
				"</div>" +
				"</div>" +
				"<div class='line' style='clear:both;'>" +
				"<span class='tname'>Tipe pengalihan</span>" +
				"<div class='info-r  ml0'>" +
				"<select class='bt-input-text mr5' name='type' style='width:100px'><option value='domain' " + (obj.type == 'domain' ? 'selected ="selected"' : "") + ">Domain</option><option value='path'  " + (obj.type == 'path' ? 'selected ="selected"' : "") + ">Path</option></select>" +
				"<span class='mlr15'>Metode pengalihan</span>" +
				"<select class='bt-input-text ml10' name='r_type' style='width:100px'><option value='301' " + (obj.r_type == '301' ? 'selected ="selected"' : "") + " >301</option><option value='302' " + (obj.r_type == '302' ? 'selected ="selected"' : "") + ">302</option></select></div>" +
				"</div>" +
				"<div class='line redirectdomain'>" +
				"<span class='tname'>Sumber pengalihan</span>" +
				"<div class='info-r  ml0'>" +
				"<input  name='from' placeholder='Nama domain atau path' class='bt-input-text mr5' type='text' style='width:200px;float: left;margin-right:0px' value='" + obj.from + "'>" +
				"<span class='tname' style='width:90px'>URL Tujuan</span>" +
				"<input  name='to' class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.to + "'>" +
				"</div>" +
				"</div>" +
				"</div>" +
				"<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-prosy'>Batal</button><button type='button' class='btn btn-sm btn-success btn-submit-redirect'>" + (type == 1 ? "Kirim" : "Simpan") + "</button></div>" +
				"</form>"
		});
		setTimeout(function () {
			$('.btn-colse-prosy').click(function () {
				layer.close(redirect_form);
			});
			$('.btn-submit-redirect').click(function () {
				var keep_path = $('[name="keep_path"]').prop('checked') ? 1 : 0;
				var r_type = $('[name="r_type"]').val();
				var type = $('[name="type"]').val();
				var from = $('[name="from"]').val();
				var to = $('[name="to"]').val();

				$.post('/site/set_redirect', {
					siteName: siteName,
					type: type,
					r_type: r_type,
					from: from,
					to: to,
					keep_path: keep_path
				}, function (res) {
					res = JSON.parse(res);
					if (res.status) {
						layer.close(redirect_form);
						to301(siteName)
					} else {
						layer.msg(res.msg, {
							icon: 2
						});
					}
				});
			});
		}, 100);
	}

	if (type == 2) {
		$.post('/site/del_redirect', {
			siteName: siteName,
			id: obj,
		}, function (res) {
			res = JSON.parse(res);
			if (res.status == true) {
				layer.msg('Berhasil dihapus', { time: 1000, icon: 1 });
				to301(siteName);
			} else {
				layer.msg(res.msg, { time: 1000, icon: 2 });
			}
		});
		return
	}

	if (type == 3) {
		var laoding = layer.load();
		var data = { siteName: siteName, id: obj };
		$.post('/site/get_redirect_conf', data, function (res) {
			layer.close(laoding);
			res = JSON.parse(res);
			if (res.status == true) {
				var mBody = "<div class='webEdit-box' style='padding: 20px'>\
				<textarea style='height: 320px; width: 445px; margin-left: 20px; line-height:18px' id='configRedirectBody'>"+ res.data.result + "</textarea>\
					<div class='info-r'>\
						<ul class='help-info-text c7 ptb10'>\
							<li>Ini file konfigurasi pengalihan, kalau nggak paham aturannya mending jangan asal ubah.</li>\
						</ul>\
					</div>\
				</div>";
				var editor;
				var index = layer.open({
					type: 1,
					title: 'Ubah file konfigurasi',
					closeBtn: 1,
					shadeClose: true,
					area: ['500px', '500px'],
					btn: ['Kirim', 'Batal'],
					content: mBody,
					success: function () {
						editor = CodeMirror.fromTextArea(document.getElementById("configRedirectBody"), {
							extraKeys: { "Ctrl-Space": "autocomplete" },
							lineNumbers: true,
							matchBrackets: true,
						});
						editor.focus();
						$(".CodeMirror-scroll").css({ "height": "300px", "margin": 0, "padding": 0 });
						$("#onlineEditFileBtn").unbind('click');
					},
					yes: function (index, layero) {
						$("#configRedirectBody").empty().text(editor.getValue());
						var load = layer.load();
						var data = {
							siteName: siteName,
							id: obj,
							config: editor.getValue(),
						};
						$.post('/site/save_redirect_conf', data, function (res) {
							layer.close(load)
							if (res.status == true) {
								layer.msg('Berhasil disimpan', { icon: 1 });
								layer.close(index);
							} else {
								layer.msg(res.msg, { time: 3000, icon: 2 });
							}
						}, 'json');
						return true;
					},
				});

			} else {
				layer.msg('Request salah!!', { time: 3000, icon: 2 });
			}
		});
		return
	}

	var body = '<div id="redirect_list" class="bt_table">\
					<div style="padding-bottom: 10px">\
						<button type="button" title="Tambah pengalihan" class="btn btn-success btn-sm mr5" onclick="to301(\''+ siteName + '\',1)" ><span>Tambah pengalihan</span></button>\
					</div>\
					<div class="divtable" style="max-height:200px;">\
						<table class="table table-hover" >\
							<thead style="position: relative;z-index: 1;">\
								<tr>\
									<th><span data-index="1"><span>Tipe pengalihan</span></span></th>\
									<th><span data-index="2"><span>Metode pengalihan</span></span></th>\
									<th><span data-index="3"><span>Simpan parameter URL</span></span></th>\
									<th><span data-index="4"><span>Aksi</span></span></th>\
								</tr>\
							</thead>\
							<tbody id="md-301-body">\
							</tbody>\
						</table>\
					</div>\
				</div>';
	$("#webedit-con").html(body);

	var loadT = layer.msg(lan.site.the_msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/get_redirect', 'siteName=' + siteName, function (res) {
		layer.close(loadT);
		$("#md-301-loading").remove();
		if (res.status === true) {
			let data = res.data.result;
			data.forEach(function (item) {
				lan_r_type = item.r_type == 0 ? "Pengalihan Permanen" : "Pengalihan Sementara"
				keep_path = item.keep_path == 0 ? "Nggak Disimpan" : "Simpan"
				let tmp = '<tr>\
					<td><span data-index="1"><span>'+ item.r_from + '</span></span></td>\
					<td><span data-index="2"><span>'+ lan_r_type + '</span></span></td>\
					<td><span data-index="2"><span>'+ keep_path + '</span></span></td>\
					<td><span data-index="4"  onclick="to301(\''+ siteName + '\', 3, \'' + item.id + '\')"  class="btlink">Detail</span> | <span data-index="5" onclick="to301(\'' + siteName + '\', 2, \'' + item.id + '\')" class="btlink">Hapus</span></td>\
				</tr>';
				$("#md-301-body").append(tmp);
			})
		} else {
			layer.msg(res.msg, { icon: 2 });
		}
	}, 'json');
}


function toProxy(siteName, type, obj) {
	if (type == 1) {
		var proxy_title = "Buat reverse proxy";
		if (typeof (obj) != 'undefined') {
			proxy_title = "Ubah reverse proxy";
		}

		layer.open({
			type: 1,
			area: '650px',
			title: proxy_title,
			closeBtn: 1,
			shift: 5,
			shadeClose: false,
			btn: ['Kirim', 'Batal'],
			content: "<form id='form_proxy' class='divtable pd15' style='padding-bottom: 10px'>\
				<div class='line'>\
					<span class='tname'>Nyalain proxy</span>\
					<div class='info-r ml0 mt5'>\
						<input name='open_proxy' class='btswitch btswitch-ios' type='checkbox' checked>\
						<label id='open_proxy' class='btswitch-btn' for='openProxy' style='float:left'></label>\
						<div style='display: inline-block'>\
							<span class='tname' style='margin-left:15px;position: relative;top: -5px;'>Cache</span>\
							<input class='btswitch btswitch-ios' type='checkbox' name='open_cache'>\
							<label class='btswitch-btn' id='open_cache' for='openCache' style='float:left'></label>\
						</div>\
					</div>\
				</div>\
				<div class='line'>\
					<span class='tname'>Nama</span>\
					<div class='info-r ml0'>\
					<input name='name' value='index' placeholder='Masukin nama' class='bt-input-text mr5' type='text' style='width:200px''>\
					</div>\
				</div>\
				<div class='line' style='display:none' id='cache_time'>\
					<span class='tname'>Waktu cache</span>\
					<div class='info-r ml0'>\
					<input name='cache_time' value='1' class='bt-input-text mr5' type='text' style='width:200px''>menit\
					</div>\
				</div>\
				<div class='line'>\
					<span class='tname'>Direktori agen</span>\
					<div class='info-r ml0'>\
					<input name='from' value='/' placeholder='/' class='bt-input-text mr5' type='text' style='width:200px''>\
					</div>\
				</div>\
				<div class='line'>\
					<span class='tname'>URL Tujuan</span>\
					<div class='info-r ml0'>\
					<input name='to' class='bt-input-text mr5' type='text' style='width:200px;float: left;margin-right:0px''>\
					<span class='tname' style='width:90px'>Kirim nama domain</span>\
					<input name='host' value='$host' class='bt-input-text mr5' type='text' style='width:200px'>\
					</div>\
				</div>\
				<input name='id' value='' type='hidden'>\
				<div class='help-info-text c7'>\
					<ul class='help-info-text c7'>\
					<li>Direktori proxy: Pas akses direktori ini, isi dari URL tujuan bakal ditampilin</li>\
					<li>URL Tujuan: Isi situs yang mau di-proxy, URL tujuan harus bisa diakses normal, kalau nggak bakal error</li>\
					<li>Kirim nama domain: Tambahin nama domain ke header request trus dikirim ke server proxy. Defaultnya pakai nama domain URL tujuan. Kalau salah atur, proxy bisa nggak jalan bener</li>\
					</ul>\
				</div>\
				</form>",
			success: function () {

				if (typeof (obj) != 'undefined') {
					// console.log(obj);
					$('input[name="name"]').val(obj['name']).attr('readonly', 'readonly').addClass('disabled');
					if (obj['open_cache'] == 'on') {
						$("input[name='open_cache']").prop("checked", true);
						$('#cache_time').show();
					}

					$('input[name="from"]').val(obj['from']);
					$('input[name="to"]').val(obj['to']);

					var url = obj['to'];
					var ip_reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
					url = url.replace(/^http[s]?:\/\//, '');
					url = url.replace(/(:|\?|\/|\\)(.*)$/, '');
					if (ip_reg.test(url)) {
						$("[name='host']").val('$host');
					} else {
						$("[name='host']").val(url);
					}

					$('input[name="id"]').val(obj['id']);
					$('input[name="cache_time"]').val(obj['cache_time']);
				}


				$('input[name="to"]').on('keyup', function () {
					var url = $(this).val();
					var ip_reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
					url = url.replace(/^http[s]?:\/\//, '');
					url = url.replace(/(:|\?|\/|\\)(.*)$/, '');
					if (ip_reg.test(url)) {
						$("[name='host']").val('$host');
					} else {
						$("[name='host']").val(url);
					}
				});

				$("#open_proxy").click(function () {
					var status = $("input[name='open_proxy']").prop("checked") == true ? 1 : 0;
					if (status == 1) {
						$("input[name='open_proxy']").prop("checked", false);
					} else {
						$("input[name='open_proxy']").prop("checked", true);
					}
				});

				$('#open_cache').click(function () {
					var status = $("input[name='open_cache']").prop("checked") == true ? 1 : 0;
					if (status == 1) {
						$('#cache_time').hide();
						$("input[name='open_cache']").prop("checked", false);
					} else {
						$('#cache_time').show();
						$("input[name='open_cache']").prop("checked", true);
					}
				});
			},
			yes: function (index, layer_ro) {
				var data = $('#form_proxy').serializeArray();
				var t = {};
				t['name'] = 'siteName';
				t['value'] = siteName;
				data.push(t);

				var loading = layer.msg('Lagi nambahin ' + proxy_title + '...', { icon: 16, time: 0, shade: [0.3, '#000'] });
				$.post('/site/set_proxy', data, function (res) {
					layer.close(loading);
					if (!res.status) {
						layer.msg(res.msg, { icon: 2, time: 10000 });
						return;
					}
					showMsg(proxy_title + " berhasil!", function () {
						layer.close(index);
						toProxy(siteName);
					}, { icon: 1, time: 2000 });
				}, 'json');
			}
		});
	}

	if (type == 2) {
		var loading = layer.msg('Lagi dihapus...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/site/del_proxy', { siteName: siteName, id: obj, }, function (res) {
			layer.close(loading);
			if (res.status == true) {
				showMsg('Berhasil dihapus', function () {
					toProxy(siteName);
				}, { time: 1000, icon: 1 });
			} else {
				layer.msg(res.msg, { time: 1000, icon: 2 });
			}
		}, 'json');
		return
	}


	if (type == 3) {
		var laoding = layer.load();
		var data = { siteName: siteName, id: obj };
		$.post('/site/get_proxy_conf', data, function (res) {
			layer.close(laoding);
			if (!res.status) {
				layer.msg('Request salah!!', { time: 3000, icon: 2 });
				return;
			}
			var mBody = "<div class='webEdit-box' style='padding: 20px'>\
			<textarea style='height: 320px; width: 445px; margin-left: 20px; line-height:18px' id='configProxyBody'>"+ res.data.result + "</textarea>\
				<div class='info-r'>\
					<ul class='help-info-text c7 ptb10'>\
						<li>Ini file konfigurasi reverse proxy, kalau nggak paham aturannya mending jangan asal ubah.</li>\
					</ul>\
				</div>\
			</div>";
			var editor;
			var index = layer.open({
				type: 1,
				title: 'Ubah file konfigurasi',
				closeBtn: 1,
				shadeClose: true,
				area: ['500px', '500px'],
				btn: ['Kirim', 'Batal'],
				content: mBody,
				success: function () {
					editor = CodeMirror.fromTextArea(document.getElementById("configProxyBody"), {
						extraKeys: { "Ctrl-Space": "autocomplete" },
						lineNumbers: true,
						matchBrackets: true,
					});
					editor.focus();
					$(".CodeMirror-scroll").css({ "height": "300px", "margin": 0, "padding": 0 });
					$("#onlineEditFileBtn").unbind('click');
				},
				yes: function (index, layero) {
					$("#configProxyBody").empty().text(editor.getValue());
					var load = layer.load();
					var data = {
						siteName: siteName,
						id: obj,
						config: editor.getValue(),
					};

					$.post('/site/save_proxy_conf', data, function (res) {
						layer.close(load)
						if (res.status == true) {
							layer.msg('Berhasil disimpan', { icon: 1 });
							layer.close(index);
						} else {
							layer.msg(res.msg, { time: 3000, icon: 2 });
						}
					}, 'json');
					return true;
				},
			});
		}, 'json');
		return;
	}

	if (type == 10 || type == 11) {
		status = type == 10 ? '0' : '1';
		var loading = layer.msg(lan.site.the_msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/site/set_proxy_status', { siteName: siteName, 'status': status, 'id': obj }, function (rdata) {
			layer.close(loading);
			if (!rdata.status) {
				layer.msg(res.msg, { time: 3000, icon: 2 });
				return;
			}
			showMsg("Berhasil diatur", function () {
				toProxy(siteName);
			}, { icon: 1, time: 2000 });
		}, 'json');
		return;
	}

	if (type == 20 || type == 21) {
		var status = type == 20 ? 'on' : '';
		obj['open_cache'] = status;
		obj['siteName'] = siteName;

		var loading = layer.msg('Lagi kirim request...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/site/set_proxy', obj, function (rdata) {
			layer.close(loading);
			if (!rdata.status) {
				layer.msg(rdata.msg, { icon: 2, time: 2000 });
				return;
			}

			showMsg("Berhasil diatur!", function () {
				toProxy(siteName);
			}, { icon: 1, time: 2000 });
		}, 'json');
		return;
	}

	var body = '<div id="proxy_list" class="bt_table">\
					<div style="padding-bottom: 10px">\
						<button type="button" title="Tambah reverse proxy" class="btn btn-success btn-sm mr5" onclick="toProxy(\''+ siteName + '\',1)" ><span>Tambah reverse proxy</span></button>\
					</div>\
					<div class="divtable" style="max-height:200px;">\
						<table class="table table-hover" >\
							<thead style="position: relative;z-index: 1;">\
								<tr>\
									<th>Nama</th>\
									<th>Direktori agen</th>\
									<th>Alamat tujuan</th>\
									<th>Cache</th>\
									<th>Status</th>\
									<th>Aksi</th>\
								</tr>\
							</thead>\
							<tbody id="md-301-body"></tbody>\
						</table>\
					</div>\
				</div>';
	$("#webedit-con").html(body);

	var loading = layer.msg(lan.site.the_msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post("/site/get_proxy_list", { siteName: siteName }, function (res) {
		layer.close(loading);
		if (!res.status) {
			layer.msg(res.msg, { icon: 2 });
			return;
		}

		var data = res.data.result;
		for (var i = 0; i < data.length; i++) {
			var item = data[i];

			var switchProxy = '<span onclick="toProxy(\'' + siteName + '\', 10, \'' + item.id + '\')" style="color:rgb(92, 184, 92);" class="btlink glyphicon glyphicon-play"></span>';
			if (!item['status']) {
				switchProxy = '<span onclick="toProxy(\'' + siteName + '\', 11, \'' + item.id + '\')" style="color:rgb(255, 0, 0);" class="btlink glyphicon glyphicon-pause"></span>';
			}

			var openCache = '<span  data-index="' + i + '" class="btlink cache off">Berhenti</span>';
			if (item['open_cache'] == 'on') {
				openCache = '<span  data-index="' + i + '" class="btlink cache on">Mulai</span>';
			}

			let tmp = '<tr>\
				<td>'+ item.name + '</td>\
				<td>'+ item.from + '</td>\
				<td>'+ item.to + '</td>\
				<td>'+ openCache + '</td>\
				<td>'+ switchProxy + '</td>\
				<td>\
				   <span data-index="'+ i + '" class="btlink detail">Detail</span> |\
				   <span data-index="'+ i + '" class="btlink edit">Ubah</span> |\
				   <span data-index="'+ i + '" class="btlink delete">Hapus</span>\
				</td>\
			</tr>';
			$("#md-301-body").append(tmp);
		}
		$('#md-301-body .detail').click(function () {
			var index = $(this).data('index');
			toProxy(siteName, 3, data[index]['id']);
		});

		$('#md-301-body .edit').click(function () {
			var index = $(this).data('index');
			toProxy(siteName, 1, data[index]);
		});

		$('#md-301-body .delete').click(function () {
			var index = $(this).data('index');
			toProxy(siteName, 2, data[index]['id']);
		});

		$('#md-301-body .cache').click(function () {
			var index = $(this).data('index');
			if ($(this).hasClass('on')) {
				toProxy(siteName, 21, data[index]);
			} else {
				toProxy(siteName, 20, data[index]);
			}
		});
	}, 'json');
}

function sslAdmin(siteName) {
	var loadT = layer.msg('Lagi ngerjain tugas...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.get('/site/get_cert_list', function (data) {
		layer.close(loadT);
		var rdata = data['data'];
		var tbody = '';
		for (var i = 0; i < rdata.length; i++) {
			tbody += '<tr><td>' + rdata[i].subject + '</td>\
				<td>'+ rdata[i].dns.join('<br>') + '</td>\
				<td>'+ rdata[i].notAfter + '</td>\
				<td>'+ rdata[i].issuer.split(' ')[0] + '</td>\
				<td style="text-align: right;"><a onclick="setCertSsl(\''+ rdata[i].subject + '\',\'' + siteName + '\')" class="btlink">Deploy</a> | <a onclick="removeSsl(\'' + rdata[i].subject + '\')" class="btlink">Hapus</a></td>\
			</tr>'
		}
		var txt = '<div class="mtb15" style="line-height:30px">\
		<button style="margin-bottom: 7px;display:none;" class="btn btn-success btn-sm">Tambah</button>\
		<div class="divtable"><table class="table table-hover"><thead><tr><th>Domain</th><th>Nama Terpercaya</th><th>Kedaluwarsa</th><th>Merek</th><th class="text-right" width=" 75">Aksi</th></tr></thead>\
		<tbody>'+ tbody + '</tbody>\
		</table></div></div>';
		$(".tab-con").html(txt);
	}, 'json');
}

function removeSsl(certName) {
	safeMessage('Hapus sertifikat', 'Yakin mau hapus sertifikat dari folder sertifikat?', function () {
		var loadT = layer.msg(lan.site.the_msg, { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/site/remove_cert', { certName: certName }, function (rdata) {
			layer.close(loadT);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			$("#ssl_admin").click();
		}, 'json');
	});
}

function setCertSsl(certName, siteName) {
	var loadT = layer.msg('Lagi deploy sertifikat...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/set_cert_to_site', { certName: certName, siteName: siteName }, function (rdata) {
		layer.close(loadT);
		showMsg(rdata.msg, function () {
			$(".tab-nav span:first-child").click();
		}, { icon: rdata.status ? 1 : 2 }, 2000);
	}, 'json');
}

function setSSL(id, siteName) {
	var sslHtml = '<div class="warning_info mb10" style="display:none;"><p class="">Peringatan: Situs ini belum pakai sertifikat SSL, akses ke situs mungkin berisiko. <button class="btn btn-success btn-xs ml10 cutTabView">Ajukan sertifikat</button></p></div>\
				<div class="tab-nav" style="margin-top: 10px;">\
					<span class="on" id="now_ssl" onclick="opSSL(\'now\','+ id + ',\'' + siteName + '\')">Sertifikat sekarang - <i class="error">[SSL belum dideploy]</i></span>\
					<span onclick="opSSL(\'lets\','+ id + ',\'' + siteName + '\')">Let\'s Encrypt</span>\
					<span onclick="opSSL(\'acme\','+ id + ',\'' + siteName + '\')">ACME</span>\
					<span id="ssl_admin" onclick="sslAdmin(\''+ siteName + '\')">Folder sertifikat</span>'
		+ '<div class="ss-text pull-right mr30" style="position: relative;top:-4px">\
	                </div></div>'
		+ '<div class="tab-con" style="padding: 0px;"></div>';
	$("#webedit-con").html(sslHtml);
	$(".tab-nav span").click(function () {
		$(this).addClass("on").siblings().removeClass("on");
	});
	opSSL('now', id, siteName);
}

function httpToHttps(siteName) {
	var isHttps = $("#toHttps").prop('checked');
	if (isHttps) {
		layer.confirm('Setelah mematikan HTTPS wajib, kamu perlu bersihin cache browser biar efeknya kerasa, lanjut?', { icon: 3, title: "Matikan Paksa HTTPS" }, function () {
			$.post('/site/close_to_https', 'siteName=' + siteName, function (rdata) {
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			}, 'json');
		});
	} else {
		$.post('/site/http_to_https', 'siteName=' + siteName, function (rdata) {
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		}, 'json');
	}
}


function deleteSSL(type, id, siteName) {
	$.post('/site/delete_ssl', 'site_name=' + siteName + '&ssl_type=' + type, function (rdata) {
		showMsg(rdata.msg, function () {
			opSSL(type, id, siteName);
		}, { icon: rdata.status ? 1 : 2 }, 2000);
	}, 'json');
}

function deploySSL(type, id, siteName) {
	$.post('/site/deploy_ssl', 'site_name=' + siteName + '&ssl_type=' + type, function (rdata) {
		showMsg(rdata.msg, function () {
			if (rdata.status) {
				$('#now_ssl').click();
			} else {
				opSSL(type, id, siteName);
			}
		}, { icon: rdata.status ? 1 : 2 }, 2000);
	}, 'json');
}

function renewSSL(type, id, siteName) {
	showSpeedWindow('Lagi perpanjang...', 'site.get_let_logs', function (layers, index) {
		$.post('/site/renew_ssl', 'site_name=' + siteName + '&ssl_type=' + type, function (rdata) {
			showMsg(rdata.msg, function () {
				if (rdata.status) {
					layer.close(index);
					opSSL(type, id, siteName);
				}
			}, { icon: rdata.status ? 1 : 2 }, 2000);
		}, 'json');
	});
}

//SSL
function opSSL(type, id, siteName, callback) {

	var now = '<div class="myKeyCon ptb15">\
	 				<div class="ssl_state_info" style="display:none;"></div>\
					<div class="custom_certificate_info">\
						<div class="ssl-con-key pull-left mr20">Key (KEY)<br><textarea id="key" class="bt-input-text"></textarea></div>\
						<div class="ssl-con-key pull-left">Sertifikat (format PEM)<br><textarea id="csr" class="bt-input-text"></textarea></div>\
					</div>\
					<div class="ssl-btn pull-left mtb15" style="width:100%">\
						<button class="btn btn-success btn-sm" onclick="saveSSL(\''+ siteName + '\')">Simpan</button>\
					</div>\
				</div>\
				<ul class="help-info-text c7 pull-left">\
					<li>Tempel isi *.key dan *.pem kamu, terus simpan.</li>\
					<li>Kalau browser bilang rantai sertifikat nggak lengkap, coba cek sertifikat PEM udah digabung dengan bener atau belum</li><li>Sertifikat format PEM = sertifikat domain.crt + sertifikat root (root_bundle).crt</li>\
					<li>Kalau situs default SSL nggak ditentukan, situs tanpa SSL bakal langsung akses situs yang ada SSL-nya pakai HTTPS</li>\
				</ul>';

	var lets = '<div class="apply_ssl">\
					<div class="label-input-group">\
						<div class="line mtb10">\
							<form>\
								<span class="tname text-center">Ways of identifying</span>\
								<div style="margin-top:7px;display:inline-block">\
									<input type="radio" name="c_type" onclick="file_check()" id="check_file" checked="checked" />\
				  					<label class="mr20" for="check_file" style="font-weight:normal">File verification</label></label>\
				  				</div>\
				  			</form>\
				  		</div>\
			  			<div class="check_message line">\
			  				<div style="margin-left:100px">\
			  					<input type="checkbox" name="checkDomain" id="checkDomain" checked="">\
			  					<label class="mr20" for="checkDomain" style="font-weight:normal">Verify the domain name in advance (find problems in advance and reduce the failure rate)</label>\
			  				</div>\
			  			</div>\
			  		</div>\
			  		<div class="line mtb10">\
			  			<span class="tname text-center">Admin mailbox</span>\
			  			<input class="bt-input-text" style="width:240px;" type="text" name="admin_email" />\
			  		</div>\
			  		<div class="line mtb10">\
			  			<span class="tname text-center">Domain</span>\
			  			<ul id="ymlist" style="padding: 5px 10px;max-height:180px;overflow:auto; width:240px;border:#ccc 1px solid;border-radius:3px"></ul>\
			  		</div>\
			  		<div class="line mtb10" style="margin-left:100px">\
			  			<button class="btn btn-success btn-sm letsApply">Apply</button>\
			  		</div>\
				  	<ul class="help-info-text c7" id="lets_help">\
				  		<li>Sebelum ajukan, pastiin domain udah di-resolve, kalau nggak bakal gagal pas direview</li>\
				  		<li>Sertifikat gratis Let\'s Encrypt, berlaku 3 bulan, bisa buat banyak domain. Otomatis diperpanjang sendiri</li>\
				  		<li>Kalau situs kamu pakai CDN atau pengalihan 301, perpanjangannya bakal gagal</li>\
				  		<li>Kalau situs default SSL nggak ditentukan, situs tanpa SSL bakal langsung akses situs yang ada SSL-nya pakai HTTPS</li>\
				  	</ul>\
			  </div>';

	var acme = '<div class="apply_ssl">\
					<div class="label-input-group">\
						<div class="line mtb10">\
							<form>\
								<span class="tname text-center">Ways of identifying</span>\
								<div style="margin-top:7px;display:inline-block">\
									<input type="radio" name="c_type" onclick="file_check()" id="check_file" checked="checked" />\
				  					<label class="mr20" for="check_file" style="font-weight:normal">File verification</label></label>\
				  				</div>\
				  			</form>\
				  		</div>\
			  			<div class="check_message line">\
			  				<div style="margin-left:100px">\
			  					<input type="checkbox" name="checkDomain" id="checkDomain" checked="">\
			  					<label class="mr20" for="checkDomain" style="font-weight:normal">Verify the domain name in advance (find problems in advance and reduce the failure rate)</label>\
			  				</div>\
			  			</div>\
			  		</div>\
			  		<div class="line mtb10">\
			  			<span class="tname text-center">Admin mailbox</span>\
			  			<input class="bt-input-text" style="width:240px;" type="text" name="admin_email" />\
			  		</div>\
			  		<div class="line mtb10">\
			  			<span class="tname text-center">Domain</span>\
			  			<ul id="ymlist" style="padding: 5px 10px;max-height:180px;overflow:auto; width:240px;border:#ccc 1px solid;border-radius:3px"></ul>\
			  		</div>\
			  		<div class="line mtb10" style="margin-left:100px">\
			  			<button class="btn btn-success btn-sm letsApply">Apply</button>\
			  		</div>\
				  	<ul class="help-info-text c7" id="lets_help">\
				  		<li>Sebelum ajukan, pastiin domain udah di-resolve, kalau nggak bakal gagal pas direview</li>\
			  			<li>ACME bisa ajukan sertifikat gratis, berlaku 3 bulan, dan bisa buat banyak domain. Otomatis diperpanjang sendiri</li>\
			  			<li>Kalau situs kamu pakai CDN atau pengalihan 301, perpanjangannya bakal gagal</li>\
			  			<li>Kalau situs default SSL nggak ditentukan, situs tanpa SSL bakal langsung akses situs yang ada SSL-nya pakai HTTPS</li></ul>\
				  	</ul>\
			  </div>';


	switch (type) {
		case 'lets':
			$(".tab-con").html(lets);
			$.post('/site/get_ssl', 'site_name=' + siteName + '&ssl_type=lets', function (data) {
				var rdata = data['data'];
				if (rdata.csr == false) {
					$.post('/site/get_site_domains', 'id=' + id, function (rdata) {
						var data = rdata['data'];
						var opt = '';
						for (var i = 0; i < data.domains.length; i++) {
							var isIP = isValidIP(data.domains[i].name);
							var x = isContains(data.domains[i].name, '*');
							if (!isIP && !x) {
								opt += '<li style="line-height:26px"><input type="checkbox" style="margin-right:5px; vertical-align:-2px" value="' + data.domains[i].name + '">' + data.domains[i].name + '</li>'
							}
						}
						$("input[name='admin_email']").val(data.email);
						$("#ymlist").html(opt);
						$("#ymlist li input").click(function (e) {
							e.stopPropagation();
						})
						$("#ymlist li").click(function () {
							var o = $(this).find("input");
							if (o.prop("checked")) {
								o.prop("checked", false)
							}
							else {
								o.prop("checked", true);
							}
						})
						$(".letsApply").click(function () {
							var c = $("#ymlist input[type='checkbox']");
							var str = [];
							var domains = '';
							for (var i = 0; i < c.length; i++) {
								if (c[i].checked) {
									str.push(c[i].value);
								}
							}
							domains = JSON.stringify(str);
							newSSL(siteName, id, domains);
						});

						if (typeof (callback) != 'undefined') {
							callback(rdata);
						}
					}, 'json');
					return;
				}
				var lets = '<div class="myKeyCon ptb15">\
						<div class="ssl_state_info" style="display:none;"></div>\
						<div class="custom_certificate_info">\
							<div class="ssl-con-key pull-left mr20" readonly>Key (KEY)<br><textarea id="key" class="bt-input-text">'+ rdata.key + '</textarea></div>\
							<div class="ssl-con-key pull-left" readonly>Sertifikat (format PEM)<br><textarea id="csr" class="bt-input-text">'+ rdata.csr + '</textarea></div>\
						</div>\
						<div class="ssl-btn pull-left mtb15" style="width:100%">\
							<button class="btn btn-success btn-sm" onclick="deploySSL(\'lets\','+ id + ',\'' + siteName + '\')">Deploy</button>\
							<button class="btn btn-success btn-sm" onclick="renewSSL(\'lets\','+ id + ',\'' + siteName + '\')">Perpanjang</button>\
							<button class="btn btn-success btn-sm" onclick="deleteSSL(\'lets\','+ id + ',\'' + siteName + '\')">Hapus</button>\
						</div>\
					</div>\
					<ul class="help-info-text c7 pull-left">\
						<li>Sertifikat gratis Let\'s Encrypt udah dibuat otomatis buat kamu</li>\
						<li>Ajukan sertifikat Let\'s Encrypt gratis, berlaku 3 bulan, dan bisa buat banyak domain. Otomatis diperpanjang sendiri</li>\
						<li>Kalau mau pakai SSL lain, silakan ganti ke sertifikat lain, tempel isi KEY dan PEM kamu, terus simpan.</li>\
					</ul>';
				$(".tab-con").html(lets);

				if (rdata['cert_data']) {
					var issuer = rdata['cert_data']['issuer'].split(" ");
					var domains = rdata['cert_data']['dns'].join("、");

					var cert_data = "<div class='state_info_flex'>\
						<div class='state_item'><span>Certificate brand：</span><span class='ellipsis_text'>"+ issuer[0] + "</span></div>\
						<div class='state_item'><span>Expire date：</span><span class='btlink'>Remaining "+ rdata['cert_data']['endtime'] + " days due</span></div>\
					</div>\
					<div class='state_info_flex'>\
						<div class='state_item'><span>Certified domain name：</span><span class='ellipsis_text'>"+ domains + "</span></div>\
					</div>";
					$(".ssl_state_info").html(cert_data);
					$(".ssl_state_info").css('display', 'block');
				}
			}, 'json');
			break;
		case 'acme':
			$(".tab-con").html(acme);
			$.post('/site/get_ssl', 'site_name=' + siteName + '&ssl_type=acme', function (data) {
				var rdata = data['data'];
				if (rdata.csr == false) {
					$.post('/site/get_site_domains', 'id=' + id, function (rdata) {
						var data = rdata['data'];
						var opt = '';
						for (var i = 0; i < data.domains.length; i++) {
							var isIP = isValidIP(data.domains[i].name);
							var x = isContains(data.domains[i].name, '*');
							if (!isIP && !x) {
								opt += '<li style="line-height:26px">\
									<input type="checkbox" style="margin-right:5px; vertical-align:-2px" value="'+ data.domains[i].name + '">' + data.domains[i].name
									+ '</li>';
							}
						}
						$("input[name='admin_email']").val(data.email);
						$("#ymlist").html(opt);
						$("#ymlist li input").click(function (e) {
							e.stopPropagation();
						})
						$("#ymlist li").click(function () {
							var o = $(this).find("input");
							if (o.prop("checked")) {
								o.prop("checked", false)
							}
							else {
								o.prop("checked", true);
							}
						})
						$(".letsApply").click(function () {
							var c = $("#ymlist input[type='checkbox']");
							var str = [];
							var domains = '';
							for (var i = 0; i < c.length; i++) {
								if (c[i].checked) {
									str.push(c[i].value);
								}
							}
							domains = JSON.stringify(str);
							newAcmeSSL(siteName, id, domains);
						});

						if (typeof (callback) != 'undefined') {
							callback(rdata);
						}
					}, 'json');
					return;
				}
				var acme = '<div class="myKeyCon ptb15">\
						<div class="ssl_state_info" style="display:none;"></div>\
						<div class="custom_certificate_info">\
							<div class="ssl-con-key pull-left mr20" readonly>Key (KEY)<br><textarea id="key" class="bt-input-text">'+ rdata.key + '</textarea></div>\
							<div class="ssl-con-key pull-left" readonly>Sertifikat (format PEM)<br><textarea id="csr" class="bt-input-text">'+ rdata.csr + '</textarea></div>\
						</div>\
						<div class="ssl-btn pull-left mtb15" style="width:100%">\
							<button class="btn btn-success btn-sm" onclick="deploySSL(\'acme\','+ id + ',\'' + siteName + '\')">Deploy</button>\
							<button class="btn btn-success btn-sm" onclick="deleteSSL(\'acme\','+ id + ',\'' + siteName + '\')">Hapus</button>\
						</div>\
					</div>\
					<ul class="help-info-text c7 pull-left">\
						<li>Sertifikat gratis ACME udah dibuat otomatis buat kamu</li>\
						<li>ACME bisa ajukan sertifikat gratis, berlaku 3 bulan, dan bisa buat banyak domain. Otomatis diperpanjang sendiri</li>\
						<li>Kalau mau pakai SSL lain, silakan ganti ke sertifikat lain, tempel isi KEY dan PEM kamu, terus simpan.</li>\
					</ul>';
				$(".tab-con").html(acme);

				if (rdata['cert_data']) {
					var issuer = rdata['cert_data']['issuer'].split(" ");
					var domains = rdata['cert_data']['dns'].join("、");

					var cert_data = "<div class='state_info_flex'>\
						<div class='state_item'><span>Certificate brand：</span><span class='ellipsis_text'>"+ issuer[0] + "</span></div>\
						<div class='state_item'><span>Expire date：</span><span class='btlink'>Remaining "+ rdata['cert_data']['endtime'] + " days due</span></div>\
					</div>\
					<div class='state_info_flex'>\
						<div class='state_item'><span>Certified domain name：</span><span class='ellipsis_text'>"+ domains + "</span></div>\
					</div>";
					$(".ssl_state_info").html(cert_data);
					$(".ssl_state_info").css('display', 'block');
				}
			}, 'json');
			break;
		case 'now':
			$(".tab-con").html(now);
			var key = '';
			var csr = '';
			var loadT = layer.msg('Lagi ngerjain tugas...', { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('site/get_ssl', 'site_name=' + siteName, function (data) {
				layer.close(loadT);
				var rdata = data['data'];

				if (rdata['cert_data']) {
					var issuer = rdata['cert_data']['issuer'].split(" ");
					var domains = rdata['cert_data']['dns'].join("、");

					var cert_data = "<div class='state_info_flex'>\
						<div class='state_item'><span>Certificate brand：</span><span class='ellipsis_text'>"+ issuer[0] + "</span></div>\
						<div class='state_item'><span>Expire date：</span><span class='btlink'>Remaining "+ rdata['cert_data']['endtime'] + " days due</span></div>\
					</div>\
					<div class='state_info_flex'>\
						<div class='state_item'><span>Certified domain name：</span><span class='ellipsis_text'>"+ domains + "</span></div>\
						<div class='state_item'><span>Force HTTPS：</span><span class='switch'>\
							<input class='btswitch btswitch-ios' id='toHttps' type='checkbox'>\
		                    <label class='btswitch-btn' for='toHttps' onclick=\"httpToHttps('" + siteName + "')\">\
						</span></div>\
					</div>";
					$(".ssl_state_info").html(cert_data);
					$(".ssl_state_info").css('display', 'block');
				}

				if (rdata.key == false) {
					rdata.key = '';
				} else {
					$(".ssl-btn").append('<button style=\'margin-left:3px;\' class="btn btn-success btn-sm" onclick="deleteSSL(\'now\',' + id + ',\'' + siteName + '\')">Hapus</button>');
				}

				if (rdata.csr == false) {
					rdata.csr = '';
				}
				$("#key").val(rdata.key);
				$("#csr").val(rdata.csr);

				$("#toHttps").attr('checked', rdata.httpTohttps);
				if (rdata.status) {
					$('.warning_info').css('display', 'none');

					$(".ssl-btn").append("<button class='btn btn-success btn-sm' onclick=\"ocSSL('close_ssl_conf','" + siteName + "')\" style='margin-left:3px;'>Matikan SSL</button>");
					$('#now_ssl').html('Sertifikat sekarang - <i style="color:#20a53a;">[SSL sudah dideploy]</i>');
				} else {
					$('.warning_info').css('display', 'block');
					$('#now_ssl').html('Sertifikat sekarang - <i style="color:red;">[SSL belum dideploy]</i>');
				}


				if (typeof (callback) != 'undefined') {
					callback(rdata);
				}
			}, 'json');
			break;
		default:
			layer.msg("Error type", { icon: 5 });
			break;
	}
}


function ocSSL(action, siteName) {
	var loadT = layer.msg('Lagi ngambil daftar sertifikat, tunggu bentar..', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post("/site/" + action, 'siteName=' + siteName + '&updateOf=1', function (rdata) {
		layer.close(loadT)

		if (!rdata.status) {
			if (!rdata.out) {
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
				setSSL(siteName);
				return;
			}
			data = "<p>Gagal ambil sertifikat：</p><hr />"
			for (var i = 0; i < rdata.out.length; i++) {
				data += "<p>Domain name: " + rdata.out[i].Domain + "</p>"
					+ "<p>Error type: " + rdata.out[i].Type + "</p>"
					+ "<p>Details: " + rdata.out[i].Detail + "</p>"
					+ "<hr />";
			}
			layer.msg(data, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
			return;
		}
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
		if (action == 'close_ssl_conf') {
			layer.msg('SSL udah dimatiin, pastiin bersihin cache browser dulu sebelum akses situs!', { icon: 1, time: 5000 });
		}
		$(".tab-nav .on").click();
	}, 'json');
}

function newSSL(siteName, id, domains) {
	showSpeedWindow('Lagi mengajukan...', 'site.get_let_logs', function (layers, index) {
		var force = '';
		if ($("#checkDomain").prop("checked")) {
			force = '&force=true';
		}
		var email = $("input[name='admin_email']").val();
		$.post('/site/create_let', 'siteName=' + siteName + '&domains=' + domains + '&email=' + email + force, function (rdata) {
			layer.close(index);
			if (rdata.status) {
				showMsg(rdata.msg, function () {
					$(".tab-nav span:first-child").click();
				}, { icon: 1 }, 2000);
				return;
			}
			layer.msg(rdata.msg, { icon: 2, area: '500px', time: 0, shade: 0.3, shadeClose: true });
		}, 'json');
	});
}

function newAcmeSSL(siteName, id, domains) {
	showSpeedWindow('Lagi mengajukan lewat ACME...', 'site.get_acme_logs', function (layers, index) {
		var force = '';
		if ($("#checkDomain").prop("checked")) {
			force = '&force=true';
		}
		var email = $("input[name='admin_email']").val();
		$.post('/site/create_acme', 'siteName=' + siteName + '&domains=' + domains + '&email=' + email + force, function (rdata) {
			layer.close(index);
			if (rdata.status) {
				showMsg(rdata.msg, function () {
					$(".tab-nav span:first-child").click();
				}, { icon: 1 }, 2000);
				return;
			}
			layer.msg(rdata.msg, { icon: 2, area: '500px', time: 0, shade: 0.3, shadeClose: true });
		}, 'json');
	});
}

function saveSSL(siteName) {
	var data = 'type=1&siteName=' + siteName + '&key=' + encodeURIComponent($("#key").val()) + '&csr=' + encodeURIComponent($("#csr").val());
	var loadT = layer.msg(lan.site.saving_txt, { icon: 16, time: 20000, shade: [0.3, '#000'] })
	$.post('/site/set_ssl', data, function (rdata) {
		layer.close(loadT);
		if (rdata.status) {
			layer.msg(rdata.msg, { icon: 1 });
			$(".ssl-btn").find(".btn-default").remove();
			$(".ssl-btn").append("<button class='btn btn-default btn-sm' onclick=\"ocSSL('close_ssl_conf','" + siteName + "')\" style='margin-left:10px'>" + lan.site.ssl_close + "</button>");
		} else {
			layer.msg(rdata.msg, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
		}
	}, 'json');
}

function phpVersion(siteName) {
	$.post('/site/get_site_php_version', 'siteName=' + siteName, function (version) {
		// console.log(version);
		if (version.status === false) {
			layer.msg(version.msg, { icon: 5 });
			return;
		}
		$.post('/site/get_php_version', function (rdata) {
			var versionSelect = "<div class='webEdit-box'>\
									<div class='line'>\
										<span class='tname' style='width:100px'>PHP version</span>\
										<div class='info-r'>\
											<select id='phpVersion' class='bt-input-text mr5' name='phpVersion' style='width:110px'>";
			var optionSelect = '';
			for (var i = 0; i < rdata.length; i++) {
				optionSelect = version.phpversion == rdata[i].version ? 'selected' : '';
				versionSelect += "<option value='" + rdata[i].version + "' " + optionSelect + ">" + rdata[i].name + "</option>"
			}
			versionSelect += "</select>\
							<button class='btn btn-success btn-sm' onclick=\"setPHPVersion('"+ siteName + "')\">Ganti</button>\
							</div>\
							<span id='php_w' style='color:red;margin-left: 32px;'></span>\
						</div>\
							<ul class='help-info-text c7 ptb10'>\
								<li>Silakan pilih versi sesuai kebutuhan program kamu</li>\
								<li>Kalau nggak butuh banget, mending jangan pakai PHP5.2 karena bisa ngurangin keamanan server kamu;</li>\
								<li>PHP7 nggak dukung ekstensi mysql, mysqli dan mysql-pdo udah terinstal secara default.</li>\
							</ul>\
						</div>\
					</div>";
			$("#webedit-con").html(versionSelect);
			$("select[name='phpVersion']").change(function () {
				if ($(this).val() == '52') {
					var msgerr = 'PHP5.2 punya risiko cross-site kalau situs kamu ada celah, mending pakai PHP5.3 ke atas!';
					$('#php_w').text(msgerr);
				} else {
					$('#php_w').text('');
				}
			})
		}, 'json');
	}, 'json');
}

function setPHPVersion(siteName) {
	var data = 'version=' + $("#phpVersion").val() + '&siteName=' + siteName;
	var loadT = layer.msg('Lagi simpan...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/set_php_version', data, function (rdata) {
		layer.close(loadT);
		layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function configFile(webSite) {
	var info = syncPost('/site/get_host_conf', { siteName: webSite });
	$.post('/files/get_body', 'path=' + info['host'], function (rdata) {
		var mBody = "<div class='webEdit-box padding-10'>\
		<textarea style='height: 320px; width: 445px; margin-left: 20px;line-height:18px' id='configBody'>"+ rdata.data.data + "</textarea>\
			<div class='info-r'>\
				<button id='SaveConfigFileBtn' class='btn btn-success btn-sm' style='margin-top:15px;'>Simpan</button>\
				<ul class='help-info-text c7 ptb10'>\
					<li>Ini file konfigurasi utama situs, kalau nggak paham aturannya mending jangan asal ubah.</li>\
				</ul>\
			</div>\
		</div>";
		$("#webedit-con").html(mBody);
		var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
			extraKeys: { "Ctrl-Space": "autocomplete" },
			lineNumbers: true,
			matchBrackets: true,
		});
		$(".CodeMirror-scroll").css({ "height": "300px", "margin": 0, "padding": 0 });
		$("#SaveConfigFileBtn").click(function () {
			$("#configBody").empty();
			$("#configBody").text(editor.getValue());
			saveConfigFile(webSite, rdata.data.encoding, info['host']);
		})
	}, 'json');
}

function saveConfigFile(webSite, encoding, path) {
	var data = 'encoding=' + encoding + '&data=' + encodeURIComponent($("#configBody").val()) + '&path=' + path;
	var loadT = layer.msg('Lagi simpan...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/save_host_conf', data, function (rdata) {
		layer.close(loadT);
		if (rdata.status) {
			layer.msg(rdata.msg, { icon: 1 });
		} else {
			layer.msg(rdata.msg, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
		}
	}, 'json');
}

function rewrite(siteName) {
	$.post("/site/get_rewrite_list", 'siteName=' + siteName, function (rdata) {
		var info = syncPost('/site/get_rewrite_conf', { siteName: siteName });
		var filename = info['rewrite'];
		$.post('/files/get_body', 'path=' + filename, function (fileBody) {
			var centent = fileBody['data']['data'];
			var rList = '';
			for (var i = 0; i < rdata.rewrite.length; i++) {
				if (i == 0) {
					rList += "<option value='0'>" + rdata.rewrite[i] + "</option>";
				} else {
					rList += "<option value='" + rdata.rewrite[i] + "'>" + rdata.rewrite[i] + "</option>";
				}
			}
			var webBakHtml = "<div class='bt-form'>\
						<div class='line'>\
						<select id='myRewrite' class='bt-input-text mr20' name='rewrite' style='width:30%;'>"+ rList + "</select>\
						<textarea class='bt-input-text' style='height: 260px; width: 480px; line-height:18px;margin-top:10px;padding:5px;' id='rewriteBody'>"+ centent + "</textarea></div>\
						<button id='SetRewriteBtn' class='btn btn-success btn-sm'>Simpan</button>\
						<button id='SetRewriteBtnTel' class='btn btn-success btn-sm'>Simpan sebagai template</button>\
						<ul class='help-info-text c7 ptb15'>\
							<li>Pilih aplikasi kamu. Kalau website nggak bisa diakses normal setelah atur aturan rewrite, coba balikin ke default</li>\
							<li>Kamu bisa ubah aturan pseudo-static dan simpan setelahnya.</li>\
						</ul>\
						</div>";
			$("#webedit-con").html(webBakHtml);

			var editor = CodeMirror.fromTextArea(document.getElementById("rewriteBody"), {
				extraKeys: { "Ctrl-Space": "autocomplete" },
				lineNumbers: true,
				matchBrackets: true,
			});

			$(".CodeMirror-scroll").css({ "height": "300px", "margin": 0, "padding": 0 });
			$("#SetRewriteBtn").click(function () {
				$("#rewriteBody").empty();
				$("#rewriteBody").text(editor.getValue());
				setRewrite(filename, encodeURIComponent(editor.getValue()));
			});
			$("#SetRewriteBtnTel").click(function () {
				$("#rewriteBody").empty();
				$("#rewriteBody").text(editor.getValue());
				setRewriteTel();
			});

			$("#myRewrite").change(function () {
				var rewriteName = $(this).val();
				if (rewriteName == '0') {
					rpath = filename;
				} else {
					var info = syncPost('/site/get_rewrite_tpl', { tplname: rewriteName });
					if (!info['status']) {
						layer.msg(info['msg']);
						return;
					}
					rpath = info['data'];
				}

				$.post('/files/get_body', 'path=' + rpath, function (fileBody) {
					$("#rewriteBody").val(fileBody['data']['data']);
					editor.setValue(fileBody['data']['data']);
				}, 'json');
			});
		}, 'json');
	}, 'json');
}

function setRewrite(filename, data) {
	var data = 'data=' + data + '&path=' + filename + '&encoding=utf-8';
	var loadT = layer.msg(lan.site.saving_txt, { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/site/set_rewrite', data, function (rdata) {
		layer.close(loadT);
		if (rdata.status) {
			layer.msg(rdata.msg, { icon: 1 });
		} else {
			layer.msg(rdata.msg, { icon: 2, time: 0, shade: 0.3, shadeClose: true });
		}
	}, 'json');
}
var aindex = null;

function setRewriteTel(act) {
	aindex = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '320px',
		title: 'Simpan sebagai template Rewrite',
		btn: [lan.public.ok, lan.public.cancel],
		content: '<div class="bt-form pd20">\
					<div class="line">\
						<input type="text" class="bt-input-text" name="rewriteName" id="rewriteName" value="" placeholder="'+ lan.site.template_name + '" style="width:100%" />\
					</div>\
				</div>',
		success: function (index) {
			$("#rewriteName").focus().keyup(function (e) {
				if (e.keyCode == 13) $("#rewriteNameBtn").click();
			});
		},
		yes: function (index) {
			name = $("#rewriteName").val();
			if (name == '') {
				layer.msg(lan.site.template_empty, { icon: 5 });
				return;
			}
			var data = 'data=' + encodeURIComponent($("#rewriteBody").val()) + '&name=' + name;
			var loadT = layer.msg(lan.site.saving_txt, { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/site/set_rewrite_tpl', data, function (rdata) {
				layer.close(loadT);
				layer.close(index);
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
			}, 'json');
			return;
		}
	});
}

function siteDefaultPage() {
	stype = getCookie('serverType');
	layer.open({
		type: 1,
		area: '460px',
		title: 'Ubah halaman default',
		closeBtn: 1,
		shift: 0,
		content: '<div class="changeDefault pd20">\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(1)">Dokumen default</button>\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(2)">Halaman error 404</button>\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(3)">Halaman kosong</button>\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(4)">Halaman Stop Situs Default</button>\
				</div>'
	});
}

function changeDefault(type) {
	$.post('/site/get_site_doc', 'type=' + type, function (rdata) {
		showMsg('Operasi berhasil!', function () {
			if (rdata.status) {
				vhref = rdata.data.path;
				onlineEditFile(0, vhref);
			}
		}, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function getClassType() {
	var select = $('.site_type > select');
	$.post('/site/get_site_types', function (rdata) {
		$(select).html('');
		$(select).append('<option value="-1">Semua Kategori</option>');
		for (var i = 0; i < rdata.length; i++) {
			$(select).append('<option value="' + rdata[i]['id'] + '">' + rdata[i]['name'] + '</option>');
		}

		$(select).bind('change', function () {
			var select_id = $(this).val();
			// console.log(select_id);
			getWeb(1, '', select_id);
		})
	}, 'json');
}
getClassType();

function setClassType() {
	$.post('/site/get_site_types', function (rdata) {
		var list = '';
		for (var i = 0; i < rdata.length; i++) {
			list += '<tr><td>' + rdata[i]['name'] + '</td>\
				<td><a class="btlink edit_type" onclick="editClassType(\''+ rdata[i]['id'] + '\',\'' + rdata[i]['name'] + '\')">Ubah</a> | <a class="btlink del_type" onclick="removeClassType(\'' + rdata[i]['id'] + '\',\'' + rdata[i]['name'] + '\')">Hapus</a>\
				</td></tr>';
		}

		layer.open({
			type: 1,
			area: '350px',
			title: 'Manajemen kategori website',
			closeBtn: 1,
			shift: 0,
			content: '<div class="bt-form edit_site_type">\
					<div class="divtable mtb15" style="overflow:auto">\
						<div class="line "><div class="info-r  ml0">\
							<input name="type_name" class="bt-input-text mr5 type_name" placeholder="Silakan isi nama kategori" type="text" style="width:50%" value=""><button name="btn_submit" class="btn btn-success btn-sm mr5 ml5 btn_submit" onclick="addClassType();">Tambah</button></div>\
						</div>\
						<table id="type_table" class="table table-hover" width="100%">\
							<thead><tr><th>Nama</th><th width="80px">Aksi</th></tr></thead>\
							<tbody>'+ list + '</tbody>\
						</table>\
					</div>\
				</div>'
		});
	}, 'json');
}

function addClassType() {
	var name = $("input[name=type_name]").val();
	$.post('/site/add_site_type', 'name=' + name, function (rdata) {
		showMsg(rdata.msg, function () {
			if (rdata.status) {
				layer.closeAll();
				setClassType();
				getClassType();
			}
		}, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function removeClassType(id, name) {
	if (id == 0) {
		layer.msg('Kategori default nggak bisa dihapus/diubah!', { icon: 2 });
		return;
	}
	layer.confirm('Yakin mau hapus kategori ini?', { title: 'Hapus kategori [' + name + ']' }, function () {
		$.post('/site/remove_site_type', 'id=' + id, function (rdata) {
			showMsg(rdata.msg, function () {
				if (rdata.status) {
					layer.closeAll();
					setClassType();
					getClassType();
				}
			}, { icon: rdata.status ? 1 : 2 });
		}, 'json');
	});
}

function editClassType(id, name) {
	if (id == 0) {
		layer.msg('Kategori default nggak bisa dihapus/diubah!', { icon: 2 });
		return;
	}

	layer.open({
		type: 1,
		area: '350px',
		title: 'Ubah manajemen kategori [' + name + ']',
		closeBtn: 1,
		shift: 0,
		content: "<form class='bt-form bt-form pd20 pb70' id='mod_pwd'>\
                    <div class='line'>\
                        <span class='tname'>Nama Kategori</span>\
                        <div class='info-r'><input name=\"site_type_mod\" class='bt-input-text mr5' type='text' value='"+ name + "' /></div>\
                    </div>\
                    <div class='bt-form-submit-btn'>\
                        <button id='site_type_mod' type='button' class='btn btn-success btn-sm btn-title'>Kirim</button>\
                    </div>\
                  </form>"
	});

	$('#site_type_mod').unbind().click(function () {
		var _name = $('input[name=site_type_mod]').val();
		$.post('/site/modify_site_type_name', 'id=' + id + '&name=' + _name, function (rdata) {
			showMsg(rdata.msg, function () {
				if (rdata.status) {
					layer.closeAll();
					setClassType();
					getClassType();
				}
			}, { icon: rdata.status ? 1 : 2 });
		}, 'json');

	});
}


function moveClassTYpe() {
	$.post('/site/get_site_types', function (rdata) {
		var option = '';
		for (var i = 0; i < rdata.length; i++) {
			option += '<option value="' + rdata[i]['id'] + '">' + rdata[i]['name'] + '</option>';
		}

		layer.open({
			type: 1,
			area: '350px',
			title: 'Atur klasifikasi situs',
			closeBtn: 1,
			shift: 0,
			content: '<div class="bt-form edit_site_type">\
					<div class="divtable mtb15" style="overflow:auto;height:80px;">\
						<div class="line"><span class="tname">Situs default</span>\
							<div class="info-r">\
							<select class="bt-input-text mr5" name="type_id" style="width:200px">'+ option + '\
							</select>\
							</div>\
						</div>\
					</div>\
					<div class="bt-form-submit-btn"><button onclick="setSizeClassType();" type="button" class="btn btn-sm btn-success">Kirim</button></div>\
				</div>'
		});
	}, 'json');
}


function setSizeClassType() {
	var data = {};
	data['id'] = $('select[name=type_id]').val();
	var ids = [];
	$('table').find('td').find('input').each(function (i, obj) {
		checked = $(this).prop('checked');
		if (checked) {
			ids.push($(this).val());
		}
	});
	data['site_ids'] = JSON.stringify(ids);
	$.post('/site/set_site_type', data, function (rdata) {
		showMsg(rdata.msg, function () {
			if (rdata.status) {
				layer.closeAll();
			}
		}, { icon: rdata.status ? 1 : 2 });
	}, 'json');
}

function tryRestartPHP(siteName) {
	$.post('/site/get_site_php_version', 'siteName=' + siteName, function (data) {
		var phpversion = data.phpversion;

		if (phpversion == "00") {
			return
		}

		var php_sign = 'php';
		if (phpversion.indexOf('yum') > -1) {
			php_sign = 'php-yum';
			phpversion = phpversion.replace('yum', '');
		}

		if (phpversion.indexOf('apt') > -1) {
			php_sign = 'php-apt';
			phpversion = phpversion.replace('apt', '');
		}

		var reqData = { name: php_sign, func: 'restart' }
		reqData['version'] = phpversion;

		// console.log(reqData);
		var loadT = layer.msg('Mencoba restart PHP otomatis [' + phpversion + ']...', { icon: 16, time: 0, shade: 0.3 });
		$.post('/plugins/run', reqData, function (data) {
			layer.close(loadT);
			layer.msg(data.msg, { icon: data.status ? 1 : 2, time: 3000, shade: [0.3, '#000'] });
		}, 'json');
	}, 'json');
}

// console.log(lan);

function isDiskWidth(){
	var comlistWidth = $("#comlist").width();
	var bodyWidth = $(".file-box").width();
	if(comlistWidth + 530 > bodyWidth){
		$("#comlist").css({"width":bodyWidth-530+"px","height":"34px","overflow":"auto"});
	}
	else{
		$("#comlist").removeAttr("style");
	}
}

function recycleBin(type){
	$.post('/files/get_recycle_bin','',function(data){
		// console.log(rdata);
		var rdata = data['data'];
		var body = ''
		switch(type){
			case 1:
				for(var i=0;i<rdata.dirs.length;i++){
					var shortwebname = rdata.dirs[i].name.replace(/'/,"\\'");
					var shortpath = rdata.dirs[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="'+rdata.dirs[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.dirs[i].dname+'">'+shortpath+'</span></td>\
								<td>'+toSize(rdata.dirs[i].size)+'</td>\
								<td>'+getLocalTime(rdata.dirs[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(getExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname.replace('BTDB_','')+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">mysql://'+shortpath.replace('BTDB_','')+'</span></td>\
								<td>-</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'

						continue;
					}
					var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
					var shortpath = rdata.files[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class="ico ico-'+(getExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+toSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 2:
				for(var i=0;i<rdata.dirs.length;i++){
					var shortwebname = rdata.dirs[i].name.replace(/'/,"\\'");
					var shortpath = rdata.dirs[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="'+rdata.dirs[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.dirs[i].dname+'">'+shortpath+'</span></td>\
								<td>'+toSize(rdata.dirs[i].size)+'</td>\
								<td>'+getLocalTime(rdata.dirs[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 3:
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1) continue;
					var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
					var shortpath = rdata.files[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class="ico ico-'+(getExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+toSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 4:
				for(var i=0;i<rdata.files.length;i++){
					if(reisImage(getFileName(rdata.files[i].name))){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(getExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+toSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
					}
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 5:
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1) continue;
					if(!(reisImage(getFileName(rdata.files[i].name)))){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(getExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+toSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="reRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="delRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
					}
				}
				$("#RecycleBody").html(body);
				return;
		}


		var tablehtml = '<div class="re-head">\
				<div style="margin-left: 3px;" class="ss-text">\
                        <em>Tempat sampah file</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="setRecycleBin" type="checkbox" '+(rdata.status?'checked':'')+'>\
                                <label class="btswitch-btn" for="setRecycleBin" onclick="setRecycleBin()"></label>\
                        </div>\
                </div>\
				<span style="line-height: 32px; margin-left: 30px;">Catatan: Kalau tempat sampah dimatikan, file yang dihapus nggak bisa balik lagi!</span>\
                <button style="float: right" class="btn btn-default btn-sm" onclick="closeRecycleBin();">Kosongkan sampah</button>\
				</div>\
				<div class="re-con">\
					<div class="re-con-menu">\
						<p class="on" onclick="recycleBin(1)">Semua</p>\
						<p onclick="recycleBin(2)">Folder</p>\
						<p onclick="recycleBin(3)">File</p>\
						<p onclick="recycleBin(4)">Gambar</p>\
						<p onclick="recycleBin(5)">Dokumen</p>\
					</div>\
					<div class="re-con-con">\
					<div style="margin: 15px;" class="divtable">\
					<table width="100%" class="table table-hover">\
						<thead>\
							<tr>\
								<th>Nama file</th><th>Lokasi asli</th>\
								<th>Ukuran</th><th width="150">Waktu dihapus</th>\
								<th style="text-align: right;" width="110">Aksi</th>\
							</tr>\
						</thead>\
						<tbody id="RecycleBody" class="list-list">'+body+'</tbody>\
			</table></div></div></div>';
		if(type == 'open'){
			layer.open({
				type: 1,
				shift: 5,
				closeBtn: 1,
				area: ['80%','606px'],
				title: lan.files.recycle_bin_title,
				content: tablehtml
			});

			if(window.location.href.indexOf("database") != -1){
				recycleBin(6);
				$(".re-con-menu p:last-child").addClass("on").siblings().removeClass("on");
			}else{
				recycleBin(1);
			}
		}
		$(".re-con-menu p").click(function(){
			$(this).addClass("on").siblings().removeClass("on");
		})
	},'json');
}

function getFileName(name){
	var text = name.split("/");
	var n = text.length-1;
	text = text[n];
	return text;
}

function reisImage(fileName){
	var exts = ['jpg','jpeg','png','bmp','gif','tiff','ico'];
	for(var i=0; i<exts.length; i++){
		if(fileName == exts[i]) return true
	}
	return false;
}

function reRecycleBin(path,obj){
	layer.confirm(lan.files.recycle_bin_re_msg,{title:lan.files.recycle_bin_re_title,closeBtn:2,icon:3},function(){
		var loadT = layer.msg(lan.files.recycle_bin_re_the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files/re_recycle_bin','path='+encodeURIComponent(path),function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			$(obj).parents('tr').remove();
		},'json');
	});
}

function delRecycleBin(path,obj){
	layer.confirm(lan.files.recycle_bin_del_msg,{title:lan.files.recycle_bin_del_title,closeBtn:2,icon:3},function(){
		var loadT = layer.msg(lan.files.recycle_bin_del_the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files/del_recycle_bin','path='+encodeURIComponent(path),function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			$(obj).parents('tr').remove();
		},'json');
	});
}

function closeRecycleBin(){
	layer.confirm('Mengosongkan tempat sampah bakal hapus semua file di dalamnya selamanya, lanjut？',{title:'Kosongkan sampah',closeBtn:2,icon:3},function(){
		var loadT = layer.msg("<div class='myspeed'>Lagi dihapus, tunggu bentar...</div>",{icon:16,time:0,shade: [0.3, '#000']});
		setTimeout(function(){
			getSpeed('.myspeed');
		},1000);
		$.post('/files/close_recycle_bin', '', function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			$("#RecycleBody").html('');
		},'json');
	});
}


function setRecycleBin(db){
	var loadT = layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:0,shade: [0.3, '#000']});
	var data = {}
	if(db == 1){
		data = {db:db};
	}
	$.post('/files/recycle_bin',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
	},'json');
}

function openFilename(obj){
	var path = $(obj).attr('data-path');
	var ext = getSuffixName(path);

	// console.log(path,ext);
	if (inArray(ext,['html','htm','php','txt','md','js','css','scss','json','c','h','pl','py','java','log','conf','sh','json'])){
		onlineEditFile(0, path);
	}

	if (inArray(ext,['png','jpeg','gif','jpg','ico'])){
        getImage(path);
	}

	if (inArray(ext,['svg'])){

		$.post("/files/get_body", "path=" + encodeURIComponent(path), function(rdata) {
			if (rdata.data.status){
				layer.open({
					type:1,
					closeBtn: 1,
					title:"Pratinjau SVG",
					area: '400px',
					shadeClose: true,
					content: '<div class="showpicdiv">'+rdata.data.data+'</div>'
				});
			} else {
				layer.msg("Tidak bisa ditampilkan");
			}
		},'json');
	}
}

function searchFile(p){
	getFiles(p);
}

function getFiles(Path) {
	var searchtype = Path;
	if(isNaN(Path)){
		var p = 1;
		Path = encodeURIComponent(Path);
	} else {
		var p = Path;
		Path = getCookie('open_dir_path');
		Path = encodeURIComponent(Path);
	}

	var search = '';
	var searchV = $("#SearchValue").val();
	if(searchV.length > 1 && searchtype == '1'){
		search = "&search="+searchV;
	}
	var showRow = getCookie('showRow');
	if(!showRow) {
		showRow = '100';
	}
	var body = '';
	var data = 'path=' + Path;
	var loadT = layer.load();
	var totalSize = 0;

	var search_all = '';
	var all = $('#search_all').hasClass('active');
	if(all){
		search_all = "&all=yes";
	}

	$.post('/files/get_dir?p=' + p + '&showRow=' + showRow + search + search_all, data, function(rdata) {
		layer.close(loadT);

		var rows = ['10','50','100','200','500','1000','2000'];
		var rowOption = '';
		for(var i=0;i<rows.length;i++){
			var rowSelected = '';
			if(showRow == rows[i]) rowSelected = 'selected';
			rowOption += '<option value="'+rows[i]+'" '+rowSelected+'>'+rows[i]+'</option>';
		}

		$("#filePage").html(rdata.PAGE);
		$("#filePage div").append("<span class='Pcount-item'>per halaman<select style='margin-left: 3px;margin-right: 3px;border:#ddd 1px solid' class='showRow'>"+rowOption+"</select>item</span>");
		$("#filePage .Pcount").css("left","16px");
		if(rdata.DIR == null) rdata.DIR = [];
		for (var i = 0; i < rdata.DIR.length; i++) {
			var fmp = rdata.DIR[i].split(";");
			var cnametext =fmp[0] + fmp[5];
			fmp[0] = fmp[0].replace(/'/, "\\'");
			if(cnametext.length>20){
				cnametext = cnametext.substring(0,20) + '...';
			}
			if(isChineseChar(cnametext)){
				if(cnametext.length>10){
					cnametext = cnametext.substring(0,10) + '...';
				}
			}
			var timetext ='--';
			if(getCookie('rank') == 'a'){
					$("#set_list").addClass("active");
					$("#set_icon").removeClass("active");
					body += "<tr class='folderBoxTr' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir'>\
						<td><input type='checkbox' name='id' value='"+fmp[0]+"'></td>\
						<td class='column-name'><span class='cursor' onclick=\"getFiles('" + rdata.PATH + "/" + fmp[0] + "')\">\
						<span class='ico ico-folder'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + "</a></span></td>\
						<td>"+toSize(fmp[1])+"</td>\
						<td>"+getLocalTime(fmp[2])+"</td>\
						<td>"+fmp[3]+"</td>\
						<td>"+fmp[4]+"</td>\
						<td class='editmenu'><span>\
						<a class='btlink' href='javascript:;' onclick=\"copyFile('" + rdata.PATH +"/"+ fmp[0] + "')\">Salin</a> | \
						<a class='btlink' href='javascript:;' onclick=\"cutFile('" + rdata.PATH +"/"+ fmp[0]+ "')\">Potong</a> | \
						<a class='btlink' href=\"javascript:reName(0,'" + fmp[0] + "');\">Ubah nama</a> | \
						<a class='btlink' href=\"javascript:setChmod(0,'" + rdata.PATH + "/"+fmp[0] + "');\">Izin</a> | \
						<a class='btlink' href=\"javascript:zip('" + rdata.PATH +"/" +fmp[0] + "');\">Zip</a> | \
						<a class='btlink' href='javascript:;' onclick=\"deleteDir('" + rdata.PATH +"/"+ fmp[0] + "')\">Hapus</a></span>\
					</td></tr>";
			} else {
				$("#set_icon").addClass("active");
				$("#set_list").removeClass("active");
				body += "<div class='file folderBox menufolder' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir' title='"+lan.files.file_name+"：" + fmp[0]+"&#13;"+lan.files.file_size+"："
						+ toSize(fmp[1])+"&#13;"+lan.files.file_etime+"："+getLocalTime(fmp[2])+"&#13;"+lan.files.file_auth+"："+fmp[3]+"&#13;"+lan.files.file_own+"："+fmp[4]+"'>\
						<input type='checkbox' name='id' value='"+fmp[0]+"'>\
						<div class='ico ico-folder' ondblclick=\"getFiles('" + rdata.PATH + "/" + fmp[0] + "')\"></div>\
						<div class='titleBox' onclick=\"getFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
			}
		}
		for (var i = 0; i < rdata.FILES.length; i++) {
			if(rdata.FILES[i] == null) continue;
			var fmp = rdata.FILES[i].split(";");
			var displayZip = isZip(fmp[0]);
			var bodyZip = '';
			var download = '';
			var cnametext =fmp[0] + fmp[5];
			fmp[0] = fmp[0].replace(/'/,"\\'");
			if(cnametext.length>48){
				cnametext = cnametext.substring(0,48) + '...';
			}
			if(isChineseChar(cnametext)){
				if(cnametext.length>16){
					cnametext = cnametext.substring(0,16) + '...';
				}
			}
			if(displayZip != -1){
				bodyZip = "<a class='btlink' href='javascript:;' onclick=\"unZip('" + rdata.PATH +"/" +fmp[0] + "'," + displayZip + ")\">Ekstrak</a> | ";
			}

			if(isText(fmp[0])){
				bodyZip = "<a class='btlink' href='javascript:;' onclick=\"onlineEditFile(0,'" + rdata.PATH +"/"+ fmp[0] + "')\">Edit</a> | ";
			}

			if(isImage(fmp[0])){
				download = "<a class='btlink' href='javascript:;' onclick=\"getImage('" + rdata.PATH +"/"+ fmp[0] + "')\">Lihat</a> | ";
			} else {
				download = "<a class='btlink' href='javascript:;' onclick=\"getFileBytes('" + rdata.PATH +"/"+ fmp[0] + "',"+fmp[1]+")\">Unduh</a> | ";
			}

			totalSize +=  parseInt(fmp[1]);
			if(getCookie("rank")=="a"){
				body += "<tr style='cursor:pointer;' class='folderBoxTr' data-path='" + rdata.PATH +"/"+ fmp[0] + "' filetype='" + fmp[0] + "' ondblclick='openFilename(this)'>\
					<td><input type='checkbox' name='id' value='"+fmp[0]+"'></td>\
					<td class='column-name'><span class='ico ico-"+(getExtName(fmp[0]))+"'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + "</a></td>\
					<td>" + (toSize(fmp[1])) + "</td>\
					<td>" + ((fmp[2].length > 11)?fmp[2]:getLocalTime(fmp[2])) + "</td>\
					<td>"+fmp[3]+"</td>\
					<td>"+fmp[4]+"</td>\
					<td class='editmenu'>\
					<span><a class='btlink' href='javascript:;' onclick=\"copyFile('" + rdata.PATH +"/"+ fmp[0] + "')\">Salin</a> | \
					<a class='btlink' href='javascript:;' onclick=\"cutFile('" + rdata.PATH +"/"+ fmp[0] + "')\">Potong</a> | \
					<a class='btlink' href='javascript:;' onclick=\"reName(0,'" + fmp[0] + "')\">Ubah nama</a> | \
					<a class='btlink' href=\"javascript:setChmod(0,'" + rdata.PATH +"/"+ fmp[0] + "');\">Izin</a> | \
					<a class='btlink' href=\"javascript:zip('" + rdata.PATH +"/" +fmp[0] + "');\">Zip</a> | "+bodyZip+download+"\
					<a class='btlink' href='javascript:;' onclick=\"deleteFile('" + rdata.PATH +"/"+ fmp[0] + "')\">Hapus</a>\
					</span></td>\
				</tr>";
			}
			else{
				body += "<div class='file folderBox menufile' data-path='" + rdata.PATH +"/"+ fmp[0] + "' filetype='"+fmp[0]+"' title='Nama file：" + fmp[0]+"&#13;ukuran："
					+ toSize(fmp[1])+"&#13;Diubah："+getLocalTime(fmp[2])+"&#13;Izin："+fmp[3]+"&#13;Pemilik："+fmp[4]+"' >\
					<input type='checkbox' name='id' value='"+fmp[0]+"'>\
					<div data-path='" + rdata.PATH +"/"+ fmp[0] + "' filetype='"+fmp[0]+"' class='ico ico-"+(getExtName(fmp[0]))+"' ondblclick='javascript;openFilename(this)'></div>\
					<div class='titleBox'><span class='tname'>" + fmp[0] + "</span></div>\
				</div>";
			}
		}
		var dirInfo = '(Total {1} folder dan {2} file, ukuran:'.replace('{1}',rdata.DIR.length+'').replace('{2}',rdata.FILES.length+'')+'<font id="pathSize">'
			+ (toSize(totalSize))+'<a class="btlink ml5" onClick="getPathSize()">Ambil</a></font>)';
		$("#dir_info").html(dirInfo);
		if( getCookie('rank') == 'a' ){
			var tablehtml = '<table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
						<thead>\
							<tr>\
								<th width="30"><input type="checkbox" id="setBox" placeholder=""></th>\
								<th>Nama file</th>\
								<th>Ukuran</th>\
								<th>Diubah</th>\
								<th>Izin</th>\
								<th>Pemilik</th>\
								<th style="text-align: right;" width="330">Aksi</th>\
							</tr>\
						</thead>\
						<tbody id="filesBody" class="list-list">'+body+'</tbody>\
					</table>';
			$("#fileCon").removeClass("fileList").html(tablehtml);
			$("#tipTools").width($("#fileCon").width());
		} else {
			$("#fileCon").addClass("fileList").html(body);
			$("#tipTools").width($("#fileCon").width());
		}
		$("#DirPathPlace input").val(rdata.PATH);
		var BarTools = '<div class="btn-group">\
						<button class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\
						Buat<span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">\
						<li><a href="javascript:createFile(0,\'' + Path + '\');">File baru</a></li>\
						<li><a href="javascript:createDir(0,\'' + Path + '\');">Folder baru</a></li>\
						</ul>\
					</div>';
		if (rdata.PATH != '/') {
			BarTools += ' <button onclick="javascript:backDir();" class="btn btn-default btn-sm glyphicon glyphicon-arrow-left" title="Kembali"></button>';
		}
		setCookie('open_dir_path',rdata.PATH);
		BarTools += ' <button onclick="javascript:getFiles(\'' + rdata.PATH + '\');" class="btn btn-default btn-sm glyphicon glyphicon-refresh" title="Segarkan"></button>\
			<button onclick="webShell()" title="Terminal" type="button" class="btn btn-default btn-sm"><em class="ico-cmd"></em></button>';
		var copyName = getCookie('copyFileName');
		var cutName = getCookie('cutFileName');
		var isPaste = (copyName == 'null') ? cutName : copyName;
		// console.log('isPaste:',isPaste);
		//---
		if (isPaste != 'null' && isPaste != undefined) {
			BarTools += ' <button onclick="javascript:pasteFile(\'' + (getFileName(isPaste)) + '\');" class="btn btn-Warning btn-sm">Tempel</button>';
		}

		$("#Batch").html('');
		var batchTools = '';
		var isBatch = getCookie('BatchSelected');
		if (isBatch == 1 || isBatch == '1') {
			batchTools += ' <button onclick="javascript:batchPaste();" class="btn btn-default btn-sm">Tempel Semua</button>';
		}
		$("#Batch").html(batchTools);

		$("#setBox").prop("checked", false);

		$("#BarTools").html(BarTools);

		$("input[name=id]").click(function(){
			if($(this).prop("checked")) {
				$(this).prop("checked", true);
				$(this).parents("tr").addClass("ui-selected");
			}
			else{
				$(this).prop("checked", false);
				$(this).parents("tr").removeClass("ui-selected");
			}
			showSeclect();
		});

		$("#setBox").click(function() {
			if ($(this).prop("checked")) {
				$("input[name=id]").prop("checked", true);
				$("#filesBody > tr").addClass("ui-selected");

			} else {
				$("input[name=id]").prop("checked", false);
				$("#filesBody > tr").removeClass("ui-selected");
			}
			showSeclect();
		});
		$("#filesBody .btlink").click(function(e){
			e.stopPropagation();
		});
		$("input[name=id]").dblclick(function(e){
			e.stopPropagation();
		});

		$("#fileCon").bind("contextmenu",function(e){
			return false;
		});
		bindselect();

		$("#fileCon").mousedown(function(e){
			var count = totalFile();
			if(e.which == 3) {
				if(count>1){
					rightMenuClickAll(e);
				} else {
					return;
				}
			}
		});

		$(".folderBox,.folderBoxTr").mousedown(function(e){
			// console.log(e);
			var count = totalFile();
			if(e.which == 3) {
				if(count <= 1){
					var a = $(this);
					var option = rightMenuClick(a.attr("filetype"),a.attr("data-path"),a.find("input").val());
					a.contextify(option);
				} else{
					rightMenuClickAll(e);
				}
			}
		});

		$(".showRow").change(function(){
			setCookie('showRow',$(this).val());
			getFiles(p);
		});
		pathPlaceBtn(rdata.PATH);
	},'json');
	setTimeout(function(){getCookie('open_dir_path');},200);
}

function totalFile(){
	var el = $("input[name='id']");
	var len = el.length;
	var count = 0;
	for(var i=0;i<len;i++){
		if(el[i].checked == true){
			count++;
		}
	}
	return count;
}

function bindselect(){
	$("#filesBody,#fileCon").selectable({
		autoRefresh: false,
		filter:"tr,.folderBox",
		cancel: "a,span,input,.ico-folder",
		selecting:function(e){
			$(".ui-selecting").find("input").prop("checked", true);
			showSeclect();
		},
		selected:function(e){
			$(".ui-selectee").find("input").prop("checked", false);
			$(".ui-selected", this).each(function() {
				$(this).find("input").prop("checked", true);
				showSeclect();
			});
		},
		unselecting:function(e){
			$(".ui-selectee").find("input").prop("checked", false);
			$(".ui-selecting").find("input").prop("checked", true);
			showSeclect();
			$("#rmenu").hide()
		}
	});
	$("#filesBody,#fileCon").selectable("refresh");
	$(".ico-folder").click(function(){
		$(this).parent().addClass("ui-selected").siblings().removeClass("ui-selected");
		$(".ui-selectee").find("input").prop("checked", false);
		$(this).prev("input").prop("checked", true);
		showSeclect();
	})
}

function showSeclect(){
	var count = totalFile();
	var batchTools = '';
	if(count > 1){
		batchTools = '<button onclick="javascript:batch(1);" class="btn btn-default btn-sm">Salin</button>\
		  <button onclick="javascript:batch(2);" class="btn btn-default btn-sm">Potong</button>\
		  <button onclick="javascript:batch(3);" class="btn btn-default btn-sm">Izin</button>\
		  <button onclick="javascript:batch(5);" class="btn btn-default btn-sm">Zip</button>\
		  <button onclick="javascript:batch(4);" class="btn btn-default btn-sm">Hapus</button>';
	}else{
		//setCookie('BatchSelected', null);
	}
	$("#Batch").html(batchTools);
}

$(window).scroll(function () {
	if($(window).scrollTop() > 16){
		$("#tipTools").css({"position":"fixed","top":"50px","left":"15px","box-shadow":"0 1px 10px 3px #ccc"});
	}else{
		$("#tipTools").css({"position":"absolute","top":"0","left":"0","box-shadow":"none"});
	}
});
$("#tipTools").width($(".file-box").width());
$("#PathPlaceBtn").width($(".file-box").width()-700);
$("#DirPathPlace input").width($(".file-box").width()-700);
if($(window).width()<1160){
	$("#PathPlaceBtn").width(290);
}
window.onresize = function(){
	$("#tipTools").width($(".file-box").width()-30);
	$("#PathPlaceBtn").width($(".file-box").width()-700);
	$("#DirPathPlace input").width($(".file-box").width()-700);
	if($(window).width()<1160){
		$("#PathPlaceBtn,#DirPathPlace input").width(290);
	}
	pathLeft();
	isDiskWidth();
}

function batch(type,access){
	var path = $("#DirPathPlace input").val();
	var el = document.getElementsByTagName('input');
	var len = el.length;
	var data='path='+path+'&type='+type;
	var name = 'data';
	var datas = [];

	var oldType = getCookie('BatchPaste');

	for(var i=0;i<len;i++){
		if(el[i].checked == true && el[i].value != 'on'){
			datas.push(el[i].value)
		}
	}
	data += "&data=" + encodeURIComponent(JSON.stringify(datas))

	if(type == 3 && access == undefined){
		setChmod(0,lan.files.all);
		return;
	}

	if(type < 3) setCookie('BatchSelected', '1');
	setCookie('BatchPaste',type);

	if(access == 1){
		var access = $("#access").val();
		var chown = $("#chown").val();
		data += '&access='+access+'&user='+chown;
		layer.closeAll();
	}
	if(type == 4){
		allDeleteFileSub(data,path);
		setCookie('BatchPaste',oldType);
		return;
	}

	if(type == 5){
		var names = '';
		for(var i=0;i<len;i++){
			if(el[i].checked == true && el[i].value != 'on'){
				names += el[i].value + ',';
			}
		}
		zip(names);
		return;
	}

	myloadT = layer.msg("<div class='myspeed'>Lagi diproses, tunggu bentar...</div>",{icon:16,time:0,shade: [0.3, '#000']});
	setTimeout(function(){getSpeed('.myspeed');},1000);
	// console.log(data);
	$.post('/files/set_batch_data',data,function(rdata){
		layer.close(myloadT);
		getFiles(path);
		layer.msg(rdata.msg,{icon:1});
	},'json');
}

function batchPaste(){
	var path = $("#DirPathPlace input").val();
	var type = getCookie('BatchPaste');
	var data = 'type='+type+'&path='+path;

	$.post('/files/check_exists_files',{dfile:path},function(rdata){
		var result = rdata['data'];
		if(result.length > 0){
			var tbody = '';
			for(var i=0;i<result.length;i++){
				tbody += '<tr><td>'+result[i].filename+'</td><td>'+toSize(result[i].size)+'</td><td>'+getLocalTime(result[i].mtime)+'</td></tr>';
			}
			var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>Nama file</th><th>Ukuran</th><th>Diubah</th></thead>\
						<tbody>'+tbody+'</tbody>\
						</table></div>';
			safeMessage('File berikut bakal ditimpa',mbody,function(){
				batchPasteTo(data,path);
			});
			$(".layui-layer-page").css("width","500px");
		}else{
			batchPasteTo(data,path);
		}
	},'json');
}

function batchPasteTo(data,path){
	myloadT = layer.msg("<div class='myspeed'>Lagi diproses, tunggu bentar...</div>",{icon:16,time:0,shade: [0.3, '#000']});
	setTimeout(function(){getSpeed('.myspeed');},1000);
	$.post('/files/batch_paste',data,function(rdata){
		layer.close(myloadT);
		setCookie('BatchSelected', null);
		getFiles(path);
		layer.msg(rdata.msg,{icon:1});
	},'json');
}


function getSuffixName(fileName){
	var extArr = fileName.split(".");
	var exts = ['folder','sql','c','cpp','cs','flv','css','js',
	'htm','html','java','log','mht','url','xml','ai','bmp','cdr','gif','ico',
	'jpeg','jpg','JPG','png','psd','webp','ape','avi','mkv','mov','mp3','mp4',
	'mpeg','mpg','rm','rmvb','swf','wav','webm','wma','wmv','rtf','docx','fdf','potm',
	'pptx','txt','xlsb','xlsx','7z','cab','iso','rar','zip','gz','bt','file','apk','bookfolder',
	'folder','folder-empty','fromchromefolder','documentfolder','fromphonefolder',
	'mix','musicfolder','picturefolder','videofolder','sefolder','access','mdb','accdb',
	'fla','doc','docm','dotx','dotm','dot','pdf',
	'ppt','pptm','pot','xls','csv','xlsm','scss','svg','pl','py','php','md','json','sh','conf'];
	var extLastName = extArr[extArr.length - 1];
	for(var i=0; i<exts.length; i++){
		if(exts[i]==extLastName){
			return exts[i];
		}
	}
	return 'file';
}

function getExtName(fileName){
	var extArr = fileName.split(".");
	var exts = ['folder','folder-unempty','sql','c','cpp','cs','flv','css','js',
	'htm','html','java','log','mht','php','url','xml','ai','bmp','cdr','gif','ico',
	'jpeg','jpg','JPG','png','psd','webp','ape','avi','flv','mkv','mov','mp3','mp4',
	'mpeg','mpg','rm','rmvb','swf','wav','webm','wma','wmv','rtf','docx','fdf','potm',
	'pptx','txt','xlsb','xlsx','7z','cab','iso','rar','zip','gz','bt','file','apk','bookfolder',
	'folder-empty','fromchromefolder','documentfolder','fromphonefolder',
	'mix','musicfolder','picturefolder','videofolder','sefolder','access','mdb','accdb',
	'fla','flv','doc','docm','dotx','dotm','dot','pdf','ppt','pptm','pot','xls','csv','xlsm'];
	var extLastName = extArr[extArr.length - 1];
	for(var i=0; i<exts.length; i++){
		if(exts[i]==extLastName){
			return exts[i];
		}
	}
	return 'file';
}

function ShowEditMenu(){
	$("#filesBody > tr").hover(function(){
		$(this).addClass("hover");
	},function(){
		$(this).removeClass("hover");
	}).click(function(){
		$(this).addClass("on").siblings().removeClass("on");
	});
}

function getDisk() {
	var LBody = '';
	$.get('/system/disk_info', function(rdata) {
		for (var i = 0; i < rdata.length; i++) {
			LBody += "<span onclick=\"getFiles('" + rdata[i].path + "')\">\
				<span class='glyphicon glyphicon-hdd'></span>&nbsp;" + (rdata[i].path=='/'?lan.files.path_root:rdata[i].path) + "(" + rdata[i].size[2] + ")</span>";
		}
		var trash = '<span id="recycle_bin" onclick="recycleBin(\'open\')" title="Tempat sampah" style="position: absolute; border-color: #ccc; right: 77px;">\
			<span class="glyphicon glyphicon-trash"></span>&nbsp;Tempat sampah</span>';
		$("#comlist").html(LBody+trash);
		isDiskWidth();
	},'json');
}

function backDir() {
	var str = $("#DirPathPlace input").val().replace('//','/');
	if(str.substr(str.length-1,1) == '/'){
			str = str.substr(0,str.length-1);
	}
	var Path = str.split("/");
	var back = '/';
	if (Path.length > 2) {
		var count = Path.length - 1;
		for (var i = 0; i < count; i++) {
			back += Path[i] + '/';
		}
		if(back.substr(back.length-1,1) == '/'){
			back = back.substr(0,back.length-1);
		}
		getFiles(back);
	} else {
		back += Path[0];
		getFiles(back);
	}
	setTimeout('pathPlaceBtn(getCookie("open_dir_path"));',200);
}

function createFile(type, path) {
	if (type == 1) {
		var fileName = $("#newFileName").val();
		layer.msg(lan.public.the, {
			icon: 16,
			time: 10000
		});
		$.post('/files/create_file', 'path=' + encodeURIComponent(path + '/' + fileName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			if(rdata.status){
				getFiles($("#DirPathPlace input").val());
				onlineEditFile(0,path + '/' + fileName);
			}
		},'json');
		return;
	}
	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '320px',
		title: 'Buat file baru',
		content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newFileName" value="" placeholder="Nama file" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm" onclick="layer.closeAll()">Batal</button>\
					<button id="createFileBtn" type="button" class="btn btn-success btn-sm" onclick="createFile(1,\'' + path + '\')">File baru</button>\
					</div>\
				</div>',
		success:function(){
			$("#newFileName").focus().keyup(function(e){
				if(e.keyCode == 13) $("#createFileBtn").click();
			});
		}
	});

}

function createDir(type, path) {
	if (type == 1) {
		var dirName = $("#newDirName").val();
		layer.msg('Lagi diproses, tunggu bentar...', {
			icon: 16,
			time: 10000
		});
		$.post('/files/create_dir', 'path=' + encodeURIComponent(path + '/' + dirName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			getFiles($("#DirPathPlace input").val());
		},'json');
		return;
	}
	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '320px',
		title: 'Folder baru',
		content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newDirName" value="" placeholder="Nama folder" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">Batal</button>\
					<button type="button" id="createDirBtn" class="btn btn-success btn-sm btn-title" onclick="createDir(1,\'' + path + '\')">Folder baru</button>\
					</div>\
				</div>',
		success:function(){
			$("#newDirName").focus().keyup(function(e){
				if(e.keyCode == 13) $("#createDirBtn").click();
			});
		}
	});

}

function deleteFile(fileName){
	layer.confirm(lan.get('recycle_bin_confirm',[fileName]),{title:'Hapus file',closeBtn:2,icon:3},function(){
		layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files/delete', 'path=' + encodeURIComponent(fileName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2,
			});
			getFiles($("#DirPathPlace input").val());
		},'json');
	});
}

function deleteDir(dirName){
	layer.confirm(lan.get('recycle_bin_confirm_dir',[dirName]),{title:'Hapus folder',closeBtn:2,icon:3},function(){
		layer.msg('Lagi diproses, tunggu bentar...',{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files/delete_dir', 'path=' + encodeURIComponent(dirName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			getFiles($("#DirPathPlace input").val());
		},'json');
	});
}

function allDeleteFileSub(data,path){
	layer.confirm('Beneran mau buang file-file ini ke tempat sampah?',{title:'Hapus massal',closeBtn:2,icon:3},function(){
		layer.msg("<div class='myspeed'>Lagi diproses, tunggu bentar...</div>",{icon:16,time:0,shade: [0.3, '#000']});
		setTimeout(function(){getSpeed('.myspeed');},1000);
		$.post('/files/set_batch_data',data,function(rdata){
			layer.closeAll();
			getFiles(path);
			layer.msg(rdata.msg,{icon:1});
		},'json');
	});
}

function reloadFiles(){
	setInterval(function(){
		var path = $("#DirPathPlace input").val();
		getFiles(path);
	},3000);
}

function downloadFile(action){

	if(action == 1){
		var fUrl = $("#mUrl").val();
		fUrl = encodeURIComponent(fUrl);

		var fpath = $("#dpath").val();
		fname = encodeURIComponent($("#dfilename").val());

		if (fUrl == "" ){
			layer.msg("Alamat URL nggak boleh kosong!",{icon:2});
			return;
		}

		layer.closeAll();
		layer.msg(lan.files.down_task,{time:0,icon:16,shade: [0.3, '#000']});

		$.post('/files/download_file','path='+fpath+'&url='+fUrl+'&filename='+fname,function(rdata){
			layer.closeAll();
			getFiles(fpath);
			getTaskCount();
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		},'json');
		return;
	}

	var path = $("#DirPathPlace input").val();
	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '500px',
		btn:["Ya","Nggak"],
		title: lan.files.down_title,
		content: '<form class="bt-form pd20">\
					<div class="line">\
						<span class="tname">Alamat URL:</span>\
						<input type="text" class="bt-input-text" name="url" id="mUrl" placeholder="Alamat URL" style="width:330px" />\
					</div>\
					<div class="line">\
						<span class="tname ">Unduh ke:</span>\
						<input type="text" class="bt-input-text" name="path" id="dpath" value="'+path+'" placeholder="Unduh ke" style="width:330px" />\
					</div>\
					<div class="line">\
						<span class="tname">Nama file:</span>\
						<input type="text" class="bt-input-text" name="filename" id="dfilename" value="" placeholder="Nama file" style="width:330px" />\
					</div>\
				</form>',
		success:function(){
			$("#mUrl").keyup(function(){
				durl = $(this).val();
				tmp = durl.split('/');
				$("#dfilename").val(tmp[tmp.length-1]);
			});
		},
		yes:function(){
			downloadFile(1);
		}
	});
}

function reName(type, fileName) {
	if (type == 1) {
		var path = $("#DirPathPlace input").val();
		var newFileName = encodeURIComponent(path + '/' + $("#newFileName").val());
		var oldFileName = encodeURIComponent(path + '/' + fileName);
		layer.msg(lan.public.the, {
			icon: 16,
			time: 10000
		});
		$.post('/files/mv_file', 'sfile=' + oldFileName + '&dfile=' + newFileName, function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			getFiles(path);
		},'json');
		return;
	}
	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '320px',
		title: 'Ubah nama',
		btn:["Ya","Nggak"],
		content: '<div class="bt-form pd20">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newFileName" value="' + fileName + '" placeholder="Nama file" style="width:100%" />\
					</div>\
				</div>',
		success:function(){
			$("#newFileName").focus().keyup(function(e){
				if(e.keyCode == 13) $(".layui-layer-btn0").click();
			});
		},
		yes:function(){
			reName(1,fileName.replace(/'/,"\\'"));
		}
	});

}

function cutFile(fileName) {
	var path = $("#DirPathPlace input").val();
	setCookie('cutFileName', fileName);
	setCookie('copyFileName', null);
	layer.msg('Potong', {
		icon: 1,
		time: 1000,
	});
	setTimeout(function(){
		getFiles(path);
	},1000);
}

function copyFile(fileName) {
	var path = $("#DirPathPlace input").val();
	setCookie('copyFileName', fileName);
	setCookie('cutFileName', null);
	layer.msg('Berhasil disalin', {
		icon: 1,
		time: 1000,
	});

	setTimeout(function(){
		getFiles(path);
	},1000);
}

function pasteFile(fileName) {
	var path = $("#DirPathPlace input").val();
	var copyName = getCookie('copyFileName');
	var cutName = getCookie('cutFileName');
	var filename = copyName;
	if(cutName != 'null' && cutName != undefined) filename=cutName;
	filename = filename.split('/').pop();
	$.post('/files/check_exists_files',{dfile:path,filename:filename},function(result){
		if(result.length > 0){
			var tbody = '';
			for(var i=0;i<result.length;i++){
				tbody += '<tr><td>'+result[i].filename+'</td><td>'+toSize(result[i].size)+'</td><td>'+getLocalTime(result[i].mtime)+'</td></tr>';
			}
			var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>Nama file</th><th>Ukuran</th><th>Diubah</th></thead>\
						<tbody>'+tbody+'</tbody>\
						</table></div>';
			safeMessage('File berikut bakal ditimpa',mbody,function(){
				pasteTo(path,copyName,cutName,fileName);
			});
		} else {
			pasteTo(path,copyName,cutName,fileName);
		}
	},'json');
}


function pasteTo(path,copyName,cutName,fileName){
	if (copyName != 'null' && copyName != undefined) {
		layer.msg(lan.files.copy_the, {
			icon: 16,
			time: 0,shade: [0.3, '#000']
		});

		if (copyName == path +'/'+ fileName){
			fileName = '__copy__'+ fileName;
		}

		$.post('/files/copy_file', 'sfile=' + encodeURIComponent(copyName) + '&dfile=' + encodeURIComponent(path +'/'+ fileName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			getFiles(path);
		},'json');
		setCookie('copyFileName', null);
		setCookie('cutFileName', null);
		return;
	}

	if (cutName != 'null' && cutName != undefined) {
		layer.msg(lan.files.mv_the, {
			icon: 16,
			time: 0,shade: [0.3, '#000']
		});
		$.post('/files/mv_file', 'sfile=' + encodeURIComponent(cutName) + '&dfile=' + encodeURIComponent(path + '/'+fileName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {icon: rdata.status ? 1 : 2});
			getFiles(path);
		},'json');
		setCookie('copyFileName', null);
		setCookie('cutFileName', null);
	}
}

function zip(dirName,submits) {
	var path = $("#DirPathPlace input").val();
	if(submits != undefined){
		if(dirName.indexOf(',') == -1){
			tmp = $("#sfile").val().split('/');
			sfile = encodeURIComponent(tmp[tmp.length-1]);
		}else{
			sfile = encodeURIComponent(dirName);
		}

		dfile = encodeURIComponent($("#dfile").val());
		layer.closeAll();
		layer.msg(lan.files.zip_the, {icon: 16,time: 0,shade: [0.3, '#000']});
		$.post('/files/zip', 'sfile=' + sfile + '&dfile=' + dfile + '&type=tar&path='+encodeURIComponent(path), function(rdata) {
			layer.closeAll();
			if(rdata == null || rdata == undefined){
				layer.msg(lan.files.zip_ok,{icon:1});
				getFiles(path)
				reloadFiles();
				return;
			}
			layer.msg(rdata.msg, {icon: rdata.status ? 1 : 2});
			if(rdata.status) getFiles(path);
		},'json');
		return
	}

	param = dirName;
	if(dirName.indexOf(',') != -1){
		tmp = path.split('/');
		dirName = path + '/' + tmp[tmp.length-1];
	}

	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '650px',
		title: lan.files.zip_title,
		content: '<div class="bt-form pd20 pb70">'
					+'<div class="line noborder">'
					+'<input type="text" class="form-control" id="sfile" value="' +param + '" placeholder="" style="display:none" />'
					+'<span>'+lan.files.zip_to+'</span>\
						<input type="text" class="bt-input-text" id="dfile" value="'+dirName + '.tar.gz" placeholder="'+lan.files.zip_to+'" style="width: 75%; display: inline-block; margin: 0px 10px 0px 20px;" />\
						<span class="glyphicon glyphicon-folder-open cursor" onclick="changePath(\'dfile\')"></span>'
					+'</div>'
					+'<div class="bt-form-submit-btn">'
					+'<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>'
					+'<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="zip(\'' + param + '\',1)">'+lan.files.file_menu_zip+'</button>'
					+'</div>'
				+'</div>',
		success:function(){
			$("#dfile").change(function(){
				var dfile = $(this).val()
				tmp = dfile.split('.');
				if(tmp[tmp.length-1] != 'gz'){
					var path = $("#DirPathPlace input").val();
					tmp = path.split('/');
					dfile += '/' + tmp[tmp.length-1] + '.tar.gz'
					$(this).val(dfile.replace(/\/\//g,'/'))
				}
			});
		}
	});

}

function unZip(fileName, type) {
	var path = $("#DirPathPlace input").val();
	if(type.length ==3){
		var sfile = encodeURIComponent($("#sfile").val());
		var dfile = encodeURIComponent($("#dfile").val());
		coding = $("select[name='coding']").val();
		layer.closeAll();
		layer.msg(lan.files.unzip_the, {icon: 16,time: 0,shade: [0.3, '#000']});
		$.post('/files/unzip', 'sfile=' + sfile + '&dfile=' + dfile +'&type=' + type + '&path='+encodeURIComponent(path), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {icon: rdata.status ? 1 : 2});
			getFiles(path);
		},'json');
		return
	}

	type = (type == 1) ? 'tar':'zip';
	var umpass = '';
	if(type == 'zip'){
		umpass = '<div class="line"><span class="tname">'+lan.files.zip_pass_title+'</span><input type="text" class="bt-input-text" id="unpass" value="" placeholder="'+lan.files.zip_pass_msg+'" style="width:330px" /></div>'
	}
	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 1,
		area: '490px',
		title: 'Ekstrak file',
		content: '<div class="bt-form pd20 pb70">'
			+'<div class="line unzipdiv">'
			+'<span class="tname">'+lan.files.unzip_name+'</span><input type="text" class="bt-input-text" id="sfile" value="' +fileName + '" placeholder="'+lan.files.unzip_name_title+'" style="width:330px" /></div>'
			+'<div class="line"><span class="tname">'+lan.files.unzip_to+'</span><input type="text" class="bt-input-text" id="dfile" value="'+path + '" placeholder="'+lan.files.unzip_to+'" style="width:330px" /></div>'
			+ umpass +'<div class="line"><span class="tname">'+lan.files.unzip_coding+'</span><select class="bt-input-text" name="coding">'
				+'<option value="UTF-8">UTF-8</option>'
				+'<option value="gb18030">GBK</option>'
			+'</select>'
			+'</div>'
			+'<div class="bt-form-submit-btn">'
			+'<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>'
			+'<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="unZip(\'' + fileName + '\',\''+type+'\')">'+lan.files.file_menu_unzip+'</button>'
			+'</div>'
		+'</div>'
	});
}

function isZip(fileName){
	var ext = fileName.split('.');
	var extName = ext[ext.length-1].toLowerCase();
	if( extName == 'zip') return 0;
	if( extName == 'gz' || extName == 'tgz') return 1;
	return -1;
}

function isText(fileName){
	var exts = ['rar','zip','tar.gz','gz','iso','xsl','doc','xdoc','jpeg',
		'jpg','png','gif','bmp','tiff','exe','so','7z','bz'];
	return isExts(fileName,exts)?false:true;
}

function isImage(fileName){
	var exts = ['jpg','jpeg','png','bmp','gif','tiff','ico'];
	return isExts(fileName,exts);
}

function isExts(fileName,exts){
	var ext = fileName.split('.');
	if(ext.length < 2) return false;
	var extName = ext[ext.length-1].toLowerCase();
	for(var i=0;i<exts.length;i++){
		if(extName == exts[i]) return true;
	}
	return false;
}

function getImage(fileName){
	var imgUrl = '/files/download?filename='+fileName;
	layer.open({
		type:1,
		offset: '150px',
		closeBtn: 1,
		title:"Pratinjau Gambar",
		area: '400px',
		shadeClose: true,
		content: '<div class="showpicdiv"><img style="max-width:400px;" src="'+imgUrl+'"></div>'
	});
}

function getFileBytes(fileName, fileSize){
	window.open('/files/download?filename='+encodeURIComponent(fileName));
}

function uploadFiles(){
	var path = $("#DirPathPlace input").val()+"/";
	layer.open({
		type:1,
		closeBtn: 1,
		title:lan.files.up_title,
		area: ['500px','300px'],
		shadeClose:false,
		content:'<div class="fileUploadDiv">\
				<input type="hidden" id="input-val" value="'+path+'" />\
				<input type="file" id="file_input"  multiple="true" autocomplete="off" />\
				<button type="button"  id="opt" autocomplete="off">Tambah</button>\
				<button type="button" id="up" autocomplete="off" >Unggah</button>\
				<span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
				<span style="float:right;margin-top: 9px;">\
				<font>Encoding file:</font>\
				<select id="fileCodeing" >\
					<option value="byte">Biner</option>\
					<option value="utf-8">UTF-8</option>\
					<option value="gb18030">GB2312</option>\
				</select>\
				</span>\
				<button type="button" id="filesClose" autocomplete="off" onClick="layer.closeAll()" >Tutup</button>\
				<ul id="up_box"></ul>\
			</div>'
	});
	uploadStart();
}

function setChmod(action,fileName){
	if(action == 1){
		var chmod = $("#access").val();
		var chown = $("#chown").val();
		var data = 'filename='+ encodeURIComponent(fileName)+'&user='+chown+'&access='+chmod;
		var loadT = layer.msg('Lagi diatur...',{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files/set_file_access',data,function(rdata){
			layer.close(loadT);
			if(rdata.status) layer.closeAll();
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			var path = $("#DirPathPlace input").val();
			getFiles(path)
		},'json');
		return;
	}

	var toExec = fileName == lan.files.all?'batch(3,1)':'setChmod(1,\''+fileName+'\')';
	$.post('/files/file_access','filename='+encodeURIComponent(fileName),function(rdata){
		// console.log(rdata);
		layer.open({
			type:1,
			closeBtn: 1,
			title: 'Atur izin ['+fileName+']',
			area: '400px',
			shadeClose:false,
			content:'<div class="setchmod bt-form ptb15 pb70">\
						<fieldset>\
							<legend>Pemilik</legend>\
							<p><input type="checkbox" id="owner_r" />Baca</p>\
							<p><input type="checkbox" id="owner_w" />Tulis</p>\
							<p><input type="checkbox" id="owner_x" />Eksekusi</p>\
						</fieldset>\
						<fieldset>\
							<legend>Grup</legend>\
							<p><input type="checkbox" id="group_r" />Baca</p>\
							<p><input type="checkbox" id="group_w" />Tulis</p>\
							<p><input type="checkbox" id="group_x" />Eksekusi</p>\
						</fieldset>\
						<fieldset>\
							<legend>Publik</legend>\
							<p><input type="checkbox" id="public_r" />Baca</p>\
							<p><input type="checkbox" id="public_w" />Tulis</p>\
							<p><input type="checkbox" id="public_x" />Eksekusi</p>\
						</fieldset>\
						<div class="setchmodnum"><input class="bt-input-text" type="text" id="access" maxlength="3" value="'+rdata.chmod+'">Izin，\
						<span>Pemilik\
						<select id="chown" class="bt-input-text">\
							<option value="www" '+(rdata.chown=='www'?'selected="selected"':'')+'>www</option>\
							<option value="mysql" '+(rdata.chown=='mysql'?'selected="selected"':'')+'>mysql</option>\
							<option value="root" '+(rdata.chown=='root'?'selected="selected"':'')+'>root</option>\
						</select></span></div>\
						<div class="bt-form-submit-btn">\
							<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">Batal</button>\
					        <button type="button" class="btn btn-success btn-sm btn-title" onclick="'+toExec+'" >Ya</button>\
				        </div>\
					</div>'
		});

		onAccess();
		$("#access").keyup(function(){
			onAccess();
		});

		$("input[type=checkbox]").change(function(){
			var idName = ['owner','group','public'];
			var onacc = '';
			for(var n=0;n<idName.length;n++){
				var access = 0;
				access += $("#"+idName[n]+"_x").prop('checked')?1:0;
				access += $("#"+idName[n]+"_w").prop('checked')?2:0;
				access += $("#"+idName[n]+"_r").prop('checked')?4:0;
				onacc += access;
			}
			$("#access").val(onacc);
		});

	},'json');
}

function onAccess(){
	var access = $("#access").val();
	var idName = ['owner','group','public'];
	for(var n=0;n<idName.length;n++){
		$("#"+idName[n]+"_x").prop('checked',false);
		$("#"+idName[n]+"_w").prop('checked',false);
		$("#"+idName[n]+"_r").prop('checked',false);
	}
	for(var i=0;i<access.length;i++){
		var onacc = access.substr(i,1);
		if(i > idName.length) continue;
		if(onacc > 7) $("#access").val(access.substr(0,access.length-1));
		switch(onacc){
			case '1':
				$("#"+idName[i]+"_x").prop('checked',true);
				break;
			case '2':
				$("#"+idName[i]+"_w").prop('checked',true);
				break;
			case '3':
				$("#"+idName[i]+"_x").prop('checked',true);
				$("#"+idName[i]+"_w").prop('checked',true);
				break;
			case '4':
				$("#"+idName[i]+"_r").prop('checked',true);
				break;
			case '5':
				$("#"+idName[i]+"_r").prop('checked',true);
				$("#"+idName[i]+"_x").prop('checked',true);
				break;
			case '6':
				$("#"+idName[i]+"_r").prop('checked',true);
				$("#"+idName[i]+"_w").prop('checked',true);
				break;
			case '7':
				$("#"+idName[i]+"_r").prop('checked',true);
				$("#"+idName[i]+"_w").prop('checked',true);
				$("#"+idName[i]+"_x").prop('checked',true);
				break;
		}
	}
}

function rightMenuClick(type,path,name){
	// console.log(type,path,name);
	var displayZip = isZip(type);
	var options = {items:[
		{text: "Salin", onclick: function() {copyFile(path)}},
		{text: "Potong", 	onclick: function() {cutFile(path)}},
		{text: "Ubah nama", onclick: function() {reName(0,name)}},
		{text: lan.files.file_menu_auth, onclick: function() {setChmod(0,path)}},
	 	{text: lan.files.file_menu_zip, onclick: function() {zip(path)}},
	]};
	if(type == "dir"){
		options.items.push({text: lan.files.file_menu_del, onclick: function() {
			deleteDir(path)}
		});
	}
	else if(isText(type)){
		options.items.push({text: lan.files.file_menu_edit, onclick: function() {
			onlineEditFile(0,path);
		}},{text: lan.files.file_menu_down, onclick: function() {
			getFileBytes(path);
		}},{ text: lan.files.file_menu_del, onclick: function() {
			deleteFile(path);
		}});
	}
	else if(displayZip != -1){
		options.items.push({text: lan.files.file_menu_unzip, onclick: function() {
			unZip(path,displayZip);
		}},{text: lan.files.file_menu_down, onclick: function() {
			getFileBytes(path);
		}},{text: lan.files.file_menu_del, onclick: function() {
			deleteFile(path);
		}});
	}
	else if(isImage(type)){
		options.items.push({text: lan.files.file_menu_img, onclick: function() {
			getImage(path);
		}},{text: lan.files.file_menu_down, onclick: function() {
			getFileBytes(path);
		}},{text: lan.files.file_menu_del, onclick: function() {
			deleteFile(path);
		}});
	}
	else{
		options.items.push({text: lan.files.file_menu_down, onclick: function() {
			getFileBytes(path);
		}},{text: lan.files.file_menu_del, onclick: function() {
			deleteFile(path);
		}});
	}
	return options;
}

function rightMenuClickAll(e){
	var menu = $("#rmenu");
	var windowWidth = $(window).width(),
		windowHeight = $(window).height(),
		menuWidth = menu.outerWidth(),
		menuHeight = menu.outerHeight(),
		x = (menuWidth + e.clientX < windowWidth) ? e.clientX : windowWidth - menuWidth,
		y = (menuHeight + e.clientY < windowHeight) ? e.clientY : windowHeight - menuHeight;

	menu.css('top', y)
		.css('left', x)
		.css('position', 'fixed')
		.css("z-index","1")
		.show();
}

function getPathSize(){
	var path = encodeURIComponent($("#DirPathPlace input").val());
	layer.msg("Lagi ngitung, sabar ya...",{icon:16,time:0,shade: [0.3, '#000']})
	$.post("/files/get_dir_size","path="+path,function(rdata){
		layer.closeAll();
		$("#pathSize").text(rdata.msg);
	},'json');
}

$("body").not(".def-log").click(function(){
	$("#rmenu").hide()
});

$("#DirPathPlace input").keyup(function(e){
	if(e.keyCode == 13) {
		var fpath = $(this).val();
		fpath = filterPath(fpath);
		getFiles(fpath);
	}
});

function pathPlaceBtn(path){
	var html = '';
	var title = '';
	if(path == '/'){
		html = '<li><a title="/">'+lan.files.path_root+'</a></li>';
	} else {
		var dst_path = path.split("/");
		for(var i = 0; i<dst_path.length; i++ ){
			title += dst_path[i]+'/';
			dst_path[0] = lan.files.path_root;
			html += '<li><a title="'+title+'">'+dst_path[i]+'</a></li>';
		}
	}

	html = '<div style="width:1200px;height:26px"><ul>'+html+'</ul></div>';
	$("#PathPlaceBtn").html(html);
	$("#PathPlaceBtn ul li a").click(function(e){
		var go_path = $(this).attr("title");
		if(go_path.length>1){
			if(go_path.substr(go_path.length-1,go_path.length) =='/'){
				go_path = go_path.substr(0,go_path.length-1);
			}
		}
		getFiles(go_path);
		e.stopPropagation();
	});
	pathLeft();
}

function pathLeft(){
	var UlWidth = $("#PathPlaceBtn ul").width();
	var SpanPathWidth = $("#PathPlaceBtn").width() - 50;
	var Ml = UlWidth - SpanPathWidth;
	if(UlWidth > SpanPathWidth ){
		$("#PathPlaceBtn ul").css("left",-Ml);
	}
	else{
		$("#PathPlaceBtn ul").css("left",0);
	}
}

$("#PathPlaceBtn").on("click", function(e){
	if($("#DirPathPlace").is(":hidden")){
		$("#DirPathPlace").css("display","inline");
		$("#DirPathPlace input").focus();
		$(this).hide();
	}else{
		$("#DirPathPlace").hide();
		$(this).css("display","inline");
	}
	$(document).one("click", function(){
		$("#DirPathPlace").hide();
		$("#PathPlaceBtn").css("display","inline");
	});
	e.stopPropagation();
});
$("#DirPathPlace").on("click", function(e){
	e.stopPropagation();
});

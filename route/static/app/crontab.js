var num = 0;
function getLogs(id){
	layer.msg('Fetching, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	var data='&id='+id;
	$.post('/crontab/logs', data, function(rdata){
		layer.closeAll();
		if(!rdata.status) {
			layer.msg(rdata.msg,{icon:2, time:2000});
			return;
		};
		layer.open({
			type:1,
			title:lan.crontab.task_log_title,
			area: ['60%','500px'],
			shadeClose:false,
			closeBtn:1,
			content:'<div class="setchmod bt-form pd20 pb70">'
				+'<pre id="crontab-log" style="overflow: auto; border: 0px none; line-height:23px;padding: 15px; margin: 0px; white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0px;font-family:"></pre>'
				+'<div class="bt-form-submit-btn" style="margin-top: 0px;">'
				+'<button type="button" class="btn btn-success btn-sm" onclick="closeLogs('+id+')">Empty</button>'
				+'<button type="button" class="btn btn-danger btn-sm" onclick="layer.closeAll()">Close</button>'
			    +'</div>'
			+'</div>'
		});

		setTimeout(function(){
			$("#crontab-log").html(rdata.msg);
		},200);
	},'json');
}


function getBackupName(hook_data, name){
	for (var i = 0; i < hook_data.length; i++) {
		if (hook_data[i]['name'] == 'backup_ftp'){
			return hook_data[i]['title'];
		}
	}
	return name;
}

function getCronData(page){
	var load = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post("/crontab/list?p="+page,'', function(rdata){
		layer.close(load);
		var cbody = "";
		if(rdata == ""){
			cbody="<tr><td colspan='6'>"+lan.crontab.task_empty+"</td></tr>";
		} else {
			for(var i=0;i<rdata.data.length;i++){
				var status = rdata.data[i]['status'] == '1' ?
				'<span class="btOpen" onclick="setTaskStatus(' + rdata.data[i].id + ',0)" style="color:rgb(92, 184, 92);cursor:pointer" title="Disable the scheduled task">Normal<span class="glyphicon glyphicon-play"></span></span>'
				:'<span onclick="setTaskStatus('+ rdata.data[i].id +',1)" class="btClose" style="color:red;cursor:pointer" title="Enable the scheduled task">Disabled<span style="color:rgb(255, 0, 0);" class="glyphicon glyphicon-pause"></span></span>';


				var cron_save = '--';
				if (rdata.data[i]['save'] != ''){
					cron_save = rdata.data[i]['save']+' Copy';
				}

				var cron_backupto = '-';
				if (rdata.data[i]['stype'] == 'site' || rdata.data[i]['stype']=='logs' || rdata.data[i]['stype']=='path' ||  rdata.data[i]['stype']=='database' || rdata.data[i]['stype'].indexOf('database_')>-1 ){
					cron_backupto = 'Local Disk';
					if (rdata.data[i]['backup_to'] != 'localhost'){
						cron_backupto = getBackupName(rdata['backup_hook'],rdata.data[i]['backup_to']);
					}
				}

				cbody += "<tr><td><input type='checkbox' onclick='checkSelect();' title='"+rdata.data[i].name+"' name='id' value='"+rdata.data[i].id+"'></td>\
					<td>"+rdata.data[i].name+"</td>\
					<td>"+status+"</td>\
					<td>"+rdata.data[i].type+"</td>\
					<td>"+rdata.data[i].cycle+"</td>\
					<td>"+cron_save +"</td>\
					<td>"+cron_backupto+"</td>\
					<td>"+rdata.data[i].addtime+"</td>\
					<td>\
						<a href=\"javascript:startTask("+rdata.data[i].id+");\" class='btlink'>Run</a> | \
						<a href=\"javascript:editTaskInfo('"+rdata.data[i].id+"');\" class='btlink'>Edit</a> | \
						<a href=\"javascript:getLogs("+rdata.data[i].id+");\" class='btlink'>Log</a> | \
						<a href=\"javascript:planDel("+rdata.data[i].id+" ,'"+rdata.data[i].name.replace('\\','\\\\').replace("'","\\'").replace('"','')+"');\" class='btlink'>Del</a>\
					</td>\
				</tr>";
			}
		}
		$('#cronbody').html(cbody);
		$('#softPage').html(rdata.list);
	},'json');
}

function setTaskStatus(id,status){
	var confirm = layer.confirm(status == '0'?'A scheduled task cannot continue running after it is paused. Do you really want to disable this scheduled task?':'This scheduled task is disabled, do you want to enable this scheduled task', {title:'Hint',icon:3,closeBtn:1},function(index) {
		if (index > 0) {
			var loadT = layer.msg('Setting state, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
			$.post('/crontab/set_cron_status',{id:id},function(rdata){

				if (!rdata.status){
					layer.msg(rdata.msg,{icon:rdata.status?1:2});
					return;
				}

				showMsg(rdata.msg,function(){
					layer.close(loadT);
					layer.close(confirm);
					getCronData(1);
				},{icon:rdata.status?1:2},2000);

			},'json');
		}
	});
}

function startTask(id){
	var loadT = layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	var data='id='+id;
	$.post('/crontab/start_task',data,function(rdata){
		showMsg(rdata.msg, function(){
			layer.closeAll();
		},{icon:rdata.status?1:2,time:2000});
	},'json');
}

function closeLogs(id){
	var loadT = layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	var data='id='+id;
	$.post('/crontab/del_logs',data,function(rdata){
		showMsg(rdata.msg, function(){
			layer.closeAll();
		},{icon:rdata.status?1:2,time:2000});
	},'json');
}


function planDel(id,name){
	safeMessage(lan.get('del',[name]),'Are you sure you want to delete this task?',function(){
		var load = layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
		var data='id='+id;
		$.post('/crontab/del',data,function(rdata){
			showMsg(rdata.msg, function(){
				layer.closeAll();
				getCronData(1);
			},{icon:rdata.status?1:2,time:2000});
		},'json');
	});
}

function isURL(str_url){
	var strRegex = '^(https|http|ftp|rtsp|mms)?://.+';
	var re=new RegExp(strRegex);
	if (re.test(str_url)){
		return (true);
	}else{
		return (false);
	}
}


function planAdd(){
	var name = $(".planname input[name='name']").val();
	if(name == ''){
		$(".planname input[name='name']").focus();
		layer.msg('Task name cannot be empty!',{icon:2});
		return;
	}
	$("#set-Config input[name='name']").val(name);

	var type = $(".plancycle").find("b").attr("val");
	$("#set-Config input[name='type']").val(type);


	var is1;
	var is2 = 1;
	switch(type){
		case 'day-n':
			is1=31;
			break;
		case 'hour-n':
			is1=23;
			break;
		case 'minute-n':
			is1=59;
			break;
		case 'month':
			is1=31;
			break;
	}

	var where1 = $('#excode_week b').attr('val');
	$("#set-Config input[name='where1']").val(where1);

	if(where1 > is1 || where1 < is2){
		$("#ptime input[name='where1']").focus();
		layer.msg('The form is invalid, please re-enter!',{icon:2});
		return;
	}

	var hour = $("#ptime input[name='hour']").val();
	if(hour > 23 || hour < 0){
		$("#ptime input[name='hour']").focus();
		layer.msg('Invalid hour value!',{icon:2});
		return;
	}
	$("#set-Config input[name='hour']").val(hour);
	var minute = $("#ptime input[name='minute']").val();
	if(minute > 59 || minute < 0){
		$("#ptime input[name='minute']").focus();
		layer.msg('Minute value is invalid!',{icon:2});
		return;
	}
	$("#set-Config input[name='minute']").val(minute);

	var save = $("#save").val();
	if(save < 0){
		layer.msg('Cannot have negative numbers!',{icon:2});
		return;
	}

	$("#set-Config input[name='save']").val(save);
	$("#set-Config input[name='week']").val($(".planweek").find("b").attr("val"));

	var sType = $(".planjs").find("b").attr("val");
	var sBody = encodeURIComponent($("#implement textarea[name='sBody']").val());

	if (sType == 'toShell'){
		if(sBody == ''){
			$("#implement textarea[name='sBody']").focus();
			layer.msg('Script code cannot be empty!',{icon:2});
			return;
		}
	}

	if(sType == 'toFile'){
		if($("#viewfile").val() == ''){
			layer.msg('Please select a script file!',{icon:2});
			return;
		}
	}

	var urladdress = $("#urladdress").val();
	if(sType == 'toUrl'){
		if(!isURL(urladdress)){
			layer.msg('The URL address is incorrect!',{icon:2});
			$("implement textarea[name='urladdress']").focus();
			return;
		}
	}
	// urladdress = encodeURIComponent(urladdress);
	$("#set-Config input[name='urladdress']").val(urladdress);
	$("#set-Config input[name='sType']").val(sType);
	$("#set-Config textarea[name='sBody']").val(decodeURIComponent(sBody));

	if(sType == 'site' || sType == 'database' || sType == 'path'){
		var backupTo = $(".planBackupTo").find("b").attr("val");
		$("#backupTo").val(backupTo);
	}

	var sName = $("#sName").attr("val");

	if(sName == 'backupAll'){
		var alist = $("ul[aria-labelledby='backdata'] li a");
		var dataList = new Array();
		for(var i=1;i<alist.length;i++){
			var tmp = alist[i].getAttribute('value');
			dataList.push(tmp);
		}
		if(dataList.length < 1){
			layer.msg('Object list is empty, cannot continue!',{icon:5});
			return;
		}
		allAddCrontab(dataList,0,'');
		return;
	}

	if (type == 'minute-n'){
		var where1 = $("#ptime input[name='where1']").val();
		$("#set-Config input[name='where1']").val(where1);
	}

	if (type == 'day-n'){
		var where1 = $("#ptime input[name='where1']").val();
		$("#set-Config input[name='where1']").val(where1);
	}

	if (type == 'hour-n'){
		var where1 = $("#ptime input[name='where1']").val();
		$("#set-Config input[name='where1']").val(where1);
	}

	if (type == 'month'){
		var where1 = $("#ptime input[name='where1']").val();
		$("#set-Config input[name='where1']").val(where1);
	}


	$("#set-Config input[name='sName']").val(sName);
	layer.msg('Adding, please wait...!',{icon:16,time:0,shade: [0.3, '#000']});
	var data = $("#set-Config").serialize() + '&sBody='+sBody + '&urladdress=' + urladdress;
	// console.log(data);
	$.post('/crontab/add',data,function(rdata){
		if(!rdata.status) {
			layer.msg(rdata.msg,{icon:2, time:2000});
			return;
		}

		showMsg(rdata.msg, function(){
			layer.closeAll();
			getCronData(1);
		},{icon:rdata.status?1:2}, 2000);

	},'json');
}

function allAddCrontab(dataList,successCount,errorMsg){
	if(dataList.length < 1) {
		layer.msg(lan.get('add_all_task_ok',[successCount]),{icon:1});
		return;
	}
	var loadT = layer.msg(lan.get('add',[dataList[0]]),{icon:16,time:0,shade: [0.3, '#000']});
	var sType = $(".planjs").find("b").attr("val");
	var minute = parseInt($("#set-Config input[name='minute']").val());
	var hour = parseInt($("#set-Config input[name='hour']").val());
	var sTitle = (sType == 'site')?lan.crontab.backup_site:lan.crontab.backup_database;
	if(sType == 'logs') sTitle = lan.crontab.backup_log;
	minute += 5;
	if(hour !== '' && minute > 59){
		if(hour >= 23) hour = 0;
		$("#set-Config input[name='hour']").val(hour+1);
		minute = 5;
	}
	$("#set-Config input[name='minute']").val(minute);
	$("#set-Config input[name='name']").val(sTitle + '['+dataList[0]+']');
	$("#set-Config input[name='sName']").val(dataList[0]);
	var pdata = $("#set-Config").serialize() + '&sBody=&urladdress=';
	$.ajax({
		type:'POST',
		url:'/crontab/add',
		data:pdata,
		async: true,
		success:function(frdata){
			layer.close(loadT);
			if(frdata.status){
				successCount++;
				getCronData(1);
			}else{
				if(!errorMsg){
					errorMsg = '<br><p>'+lan.crontab.backup_all_err+'</p>';
				}
				errorMsg += '<li>'+dataList[0]+' -> '+frdata.msg+'</li>'
			}

			dataList.splice(0,1);
			allAddCrontab(dataList,successCount,errorMsg);
		}
	});
}

initDropdownMenu();
function initDropdownMenu(){
	$(".dropdown ul li a").click(function(){
		var txt = $(this).text();
		var type = $(this).attr("value");
		$(this).parents(".dropdown").find("button b").text(txt).attr("val",type);
		switch(type){
			case 'day':
				closeOpt();
				toHour();
				toMinute();
				break;
			case 'day-n':
				closeOpt();
				toWhere1('Day');
				toHour();
				toMinute();
				break;
			case 'hour':
				closeOpt();
				toMinute();
				break;
			case 'hour-n':
				closeOpt();
				toWhere1('Hour');
				toMinute();
				break;
			case 'minute-n':
				closeOpt();
				toWhere1('Minute');
				break;
			case 'week':
				closeOpt();
				toWeek();
				toHour();
				toMinute();
				break;
			case 'month':
				closeOpt();
				toWhere1('Day');
				toHour();
				toMinute();
				break;
			case 'toFile':
				toFile();
				break;
			case 'toShell':
				toShell();
				$(".controls").html('Script content');
				break;
			case 'rememory':
				rememory();
				$(".controls").html('Hint');
				break;
			case 'site':
				toBackup('sites');
				$(".controls").html('Backup site');
				break;
			case 'database_mariadb':
			case 'database_postgresql':
			case 'database_mysql-apt':
			case 'database_mysql-yum':
			case 'database':
				toBackup(type);
				$(".controls").html('Backup database');
				break;
			case 'path':
				toBackup('path');
				$(".controls").html('Backup directory');
				break;
			case 'logs':
				toBackup('logs');
				$(".controls").html('Cutting log');
				break;
			case 'toUrl':
				toUrl();
				$(".controls").html('URL address');
				break;
		}
	});
}


function toBackup(type){
	var sMsg = "";
	switch(type){
		case 'sites':
			sMsg = 'Backup site';
			sType = "sites";
			break;
		case 'database_mariadb':
		case 'database_postgresql':
		case 'database_mysql-apt':
		case 'database_mysql-yum':
		case 'database':
			sMsg = 'Backup database';
			suffix = type.replace('database','')
			if (suffix != ''){
				suffix = suffix.replace('_','')
				sMsg = 'Backup database ['+suffix+']';
			}
			sType = type;
			break;
		case 'logs':
			sMsg = 'Cutting log';
			sType = "logs";
			break;
		case 'path':
			sMsg = 'Backup directory';
			sType = "path";
			break;
	}
	var data = 'type='+sType;

	$.post('/crontab/get_data_list',data,function(rdata){
		$(".planname input[name='name']").attr('readonly','true').css({"background-color":"#f6f6f6","color":"#666"});
		var sOpt = "";
		if(rdata.data.length == 0){
			layer.msg(lan.public.list_empty,{icon:2})
			return;
		}

		for(var i=0;i<rdata.data.length;i++){
			if(i==0){
				$(".planname input[name='name']").val(sMsg+'['+rdata.data[i].name+']');
			}
			sOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.data[i].name+'">'+rdata.data[i].name+'['+rdata.data[i].ps+']</a></li>';
		}


		if (sType != 'path'){
			sOpt = '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="backupAll">All</a></li>' + sOpt;
		}

		var orderOpt = '';
		for (var i=0;i<rdata.orderOpt.length;i++){
			orderOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.orderOpt[i].name+'">'+rdata.orderOpt[i].title+'</a></li>'
		}


		var changeDir = '';
		if (sType == 'path'){
			changeDir = '<span class="glyphicon glyphicon-folder-open cursor mr20 changePathDir" style="float:left;line-height: 30px;"></span>';
		}

		var sBody = '<div class="dropdown pull-left mr20 check">\
					  <button class="btn btn-default dropdown-toggle sname" type="button" id="backdata" data-toggle="dropdown" style="width:auto">\
						<b id="sName" val="'+rdata.data[0].name+'">'+rdata.data[0].name+'['+rdata.data[0].ps+']</b> <span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="backdata">'+sOpt+'</ul>\
					</div>\
					'+ changeDir +'\
					<div class="textname pull-left mr20">Backup to</div>\
					<div class="dropdown planBackupTo pull-left mr20">\
					  <button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:auto;">\
						<b val="localhost">server disk</b><span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="localhost">Server disk</a></li>\
						'+ orderOpt +'\
					  </ul>\
					</div>\
					<div class="textname pull-left mr20">Keep up to date</div><div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="save" id="save" value="3" maxlength="4" max="100" min="1"></span>\
					<span class="name">Copy</span>\
					</div>';
		$("#implement").html(sBody);
		getselectname();

		$('.changePathDir').click(function(){
			changePathCallback($('#sName').val(),function(select_dir){
				$(".planname input[name='name']").val('Backup directory ['+select_dir+']');
				$('#implement .sname b').attr('val',select_dir).text(select_dir);
			});
		});


		$(".dropdown ul li a").click(function(){
			var sName = $("#sName").attr("val");
			if(!sName) return;
			$(".planname input[name='name']").val(sMsg+'['+sName+']');
		});
	},'json');

}

function editTaskInfo(id){
	layer.msg('Fetching, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/crontab/get_crond_find',{id:id},function(rdata){
		layer.closeAll();
		// console.log('get_crond_find:', rdata);
		var sTypeName = '',sTypeDom = '',cycleName = '',cycleDom = '',weekName = '',weekDom = '',sNameName ='',sNameDom = '',backupsName = '',backupsDom ='';
		obj = {
			from:{
				id:rdata.id,
				name: rdata.name,
				type: rdata['type'],
				stype: rdata.stype,
				where1: rdata.where1,
				hour: rdata.where_hour,
				minute: rdata.where_minute,
				week: rdata.where1,
				sbody: rdata.sbody,
				sname: rdata.sname,
				backup_to: rdata.backup_to,
				save: rdata.save,
				urladdress: rdata.urladdress,
			},
			sTypeArray:[['toShell','Shell script'],['site','Backup site'],['database','Backup database'],['logs','Log cutting'],['path','Backup directory'],['rememory','Free memory'],['toUrl','Visit URL']],
			cycleArray:[['day','Every day'],['day-n','N days'],['hour','Per hour'],['hour-n','N hours'],['minute-n','N minutes'],['week','every week'],['month','per month']],
			weekArray:[[1,'Monday'],[2,'Tuesday'],[3,'Wednesday'],[4,'Thursday'],[5,'Friday'],[6,'Saturday'],[7,'Sunday']],
			sNameArray:[],
			backupsArray:[],
			create:function(callback){
				if (obj.from['stype'].indexOf('database_')>-1){
					name = obj.from['stype'].replace('database_','');
					sTypeName = 'Backup database ['+name+']';
					sTypeDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj.from['stype'] +'">'+ sTypeName +'</a></li>';
				} else {
					for(var i = 0; i <obj['sTypeArray'].length; i++){
						if(obj.from['stype'] == obj['sTypeArray'][i][0]){
							sTypeName  = obj['sTypeArray'][i][1];
						}
						sTypeDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['sTypeArray'][i][0] +'">'+ obj['sTypeArray'][i][1] +'</a></li>';
					}
				}

				for(var i = 0; i <obj['cycleArray'].length; i++){
					if(obj.from['type'] == obj['cycleArray'][i][0])  cycleName  = obj['cycleArray'][i][1];
					cycleDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['cycleArray'][i][0] +'">'+ obj['cycleArray'][i][1] +'</a></li>';
				}

				for(var i = 0; i <obj['weekArray'].length; i++){
					if(obj.from['week'] == obj['weekArray'][i][0])  weekName  = obj['weekArray'][i][1];
					weekDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['weekArray'][i][0] +'">'+ obj['weekArray'][i][1] +'</a></li>';
				}

				if(obj.from.stype == 'site' || obj.from.stype == 'database' || obj.from.stype == 'path' || obj.from.stype == 'logs' || obj.from['stype'].indexOf('database_')>-1){
					$.post('/crontab/get_data_list',{type:obj.from.stype},function(rdata){
						// console.log(rdata);
						obj.sNameArray = rdata.data;
						obj.sNameArray.unshift({name:'ALL',ps:'all'});
						obj.backupsArray = rdata.orderOpt;
						obj.backupsArray.unshift({title:'Server disk',name:'localhost'});
						for(var i = 0; i <obj['sNameArray'].length; i++){
							if(obj.from['sname'] == obj['sNameArray'][i]['name']){
								sNameName  = obj['sNameArray'][i]['ps'];
							}
							sNameDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['sNameArray'][i]['name'] +'">'+ obj['sNameArray'][i]['ps'] +'</a></li>';
						}
						for(var i = 0; i <obj['backupsArray'].length; i++){
							if(obj.from['backup_to'] == obj['backupsArray'][i]['name'])  {
								backupsName  = obj['backupsArray'][i]['title'];
							}
							backupsDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['backupsArray'][i]['name'] +'">'+ obj['backupsArray'][i]['title'] +'</a></li>';
						}
						callback();
					},'json');
				}else{
					callback();
				}
			}
		};
		obj.create(function(){

			var changeDir = '';
			if (obj.from.stype == 'path'){
				changeDir = '<span class="glyphicon glyphicon-folder-open cursor mr20 changePathDir" style="float:left;line-height: 30px;"></span>';
			}

			layer.open({
				type:1,
				title:'Edit scheduled tasks-['+rdata.name+']',
				area: ['850px','440px'],
				skin:'layer-create-content',
				shadeClose:false,
				closeBtn:1,
				content:'<div class="setting-con ptb20">\
							<div class="clearfix plan ptb10">\
								<span class="typename c4 pull-left f14 text-right mr20">Task type</span>\
								<div class="dropdown stype_list pull-left mr20">\
									<button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:auto" disabled="disabled">\
										<b val="'+ obj.from.type +'">'+ sTypeName +'</b>\
										<span class="caret"></span>\
									</button>\
									<ul class="dropdown-menu" role="menu" aria-labelledby="sType">'+ sTypeDom +'</ul>\
								</div>\
							</div>\
							<div class="clearfix plan ptb10">\
								<span class="typename c4 pull-left f14 text-right mr20">Name</span>\
								<div class="planname pull-left"><input type="text" name="name" class="bt-input-text sName_create" value="'+ obj.from.name +'"></div>\
							</div>\
							<div class="clearfix plan ptb10">\
								<span class="typename c4 pull-left f14 text-right mr20">Cycle</span>\
								<div class="dropdown  pull-left mr20">\
									<button class="btn btn-default dropdown-toggle cycle_btn" type="button" data-toggle="dropdown" style="width:94px">\
										<b val="'+ obj.from.stype +'">'+ cycleName +'</b>\
										<span class="caret"></span>\
									</button>\
									<ul class="dropdown-menu" role="menu" aria-labelledby="cycle">'+ cycleDom +'</ul>\
								</div>\
								<div class="pull-left optional_week">\
									<div class="dropdown week_btn pull-left mr20" style="display:'+ (obj.from.type == "week"  ?'block;':'none') +'">\
										<button class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown" >\
											<b val="'+ obj.from.week +'">'+ weekName +'</b> \
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="week">'+ weekDom +'</ul>\
									</div>\
									<div class="plan_hms pull-left mr20 bt-input-text where1_input" style="display:'+ (obj.from.type == "day-n" || obj.from.type == 'month' ?'block;':'none') +'"><span><input type="number" name="where1" class="where1_create" value="'+obj.from.where1 +'" maxlength="2" max="23" min="0"></span> <span class="name">Day</span> </div>\
									<div class="plan_hms pull-left mr20 bt-input-text hour_input" style="display:'+ (obj.from.type == "day" || obj.from.type == 'day-n' || obj.from.type == 'hour-n' || obj.from.type == 'week' || obj.from.type == 'month'?'block;':'none') +'"><span><input type="number" name="hour" class="hour_create" value="'+ ( obj.from.type == 'hour-n' ? obj.from.where1 : obj.from.hour ) +'" maxlength="2" max="23" min="0"></span> <span class="name">Hour</span> </div>\
									<div class="plan_hms pull-left mr20 bt-input-text minute_input"><span><input type="number" name="minute" class="minute_create" value="'+ (obj.from.type == 'minute-n' ? obj.from.where1 : obj.from.minute)+'" maxlength="2" max="59" min="0"></span> <span class="name">Minute</span> </div>\
								</div>\
							</div>\
							<div class="clearfix plan ptb10 site_list" style="display:none">\
								<span class="typename controls c4 pull-left f14 text-right mr20">'+ sTypeName  +'</span>\
								<div style="line-height:34px"><div class="dropdown pull-left mr20 sName_btn" style="display:'+ (obj.from.sType != "path"?'block;':'none') +'">\
									<button class="btn btn-default dropdown-toggle sname" type="button"  data-toggle="dropdown" style="width:auto" disabled="disabled">\
										<b id="sName" val="'+ obj.from.sname +'">'+ obj.from.sname +'</b>\
										<span class="caret"></span>\
									</button>\
									<ul class="dropdown-menu" role="menu" aria-labelledby="sName">'+ sNameDom +'</ul>\
								</div>\
								<div class="info-r" style="float: left;margin-right: 25px;display:'+ (obj.from.sType == "path"?'block;':'none') +'">\
									<input id="inputPath" class="bt-input-text mr5 " type="text" name="path" value="'+ obj.from.sName +'" placeholder="Backup directory" style="width:208px;height:33px;" disabled="disabled">\
								</div>\
								'+changeDir+'\
								<div class="textname pull-left mr20">Backup to</div>\
									<div class="dropdown  pull-left mr20">\
										<button class="btn btn-default dropdown-toggle backup_btn" type="button"  data-toggle="dropdown" style="width:auto;">\
											<b val="'+ obj.from.backup_to +'">'+ backupsName +'</b>\
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="backupTo">'+ backupsDom +'</ul>\
									</div>\
									<div class="textname pull-left mr20">Keep up to date</div>\
									<div class="plan_hms pull-left mr20 bt-input-text">\
										<span><input type="number" name="save" class="save_create" value="'+ obj.from.save +'" maxlength="4" max="100" min="1"></span><span class="name">copy</span>\
									</div>\
								</div>\
							</div>\
							<div class="clearfix plan ptb10"  style="display:'+ (obj.from.stype == "toShell"?'block;':'none') +'">\
								<span class="typename controls c4 pull-left f14 text-right mr20">Script content</span>\
								<div style="line-height:34px"><textarea class="txtsjs bt-input-text sBody_create" name="sbody">'+ obj.from.sbody +'</textarea></div>\
							</div>\
							<div class="clearfix plan ptb10" style="display:'+ (obj.from.stype == "rememory"?'block;':'none') +'">\
								<span class="typename controls c4 pull-left f14 text-right mr20">Hint</span>\
								<div style="line-height:34px">Release the memory usage of PHP, MYSQL, OpenResty, it is recommended to execute it in the middle of the night every day!</div>\
							</div>\
							<div class="clearfix plan ptb10" style="display:'+ (obj.from.stype == "toUrl"?'block;':'none') +'">\
								<span class="typename controls c4 pull-left f14 text-right mr20">URL address</span>\
								<div style="line-height:34px"><input type="text" style="width:400px; height:34px" class="bt-input-text url_create" name="urladdress"  placeholder="URL address" value="'+ obj.from.urladdress +'"></div>\
							</div>\
							<div class="clearfix plan ptb10">\
								<div class="bt-submit plan-submits " style="margin-left: 141px;">Save</div>\
							</div>\
						</div>',

				success:function(){

					$('.changePathDir').click(function(){
						changePathCallback($('#sName').val(),function(select_dir){
							$('input[name="name"]').val('Backup directory ['+select_dir+']');
							$('.sName_btn .sname b').attr('val',select_dir).text(select_dir);
							obj.from.sname = select_dir;
						});
					});

					if(obj.from.stype == 'toShell'){
						$('.site_list').hide();
					} else if (obj.from.stype == 'rememory') {
						$('.site_list').hide();
					} else if ( obj.from.stype == 'toUrl'){
						$('.site_list').hide();
					} else {
						$('.site_list').show();
					}



					obj.from.minute = $('.minute_create').val();
					obj.from.hour = $('.hour_create').val();
					obj.from.where1 = $('.where1_create').val();

					$('.sName_create').blur(function () {
						obj.from.name = $(this).val();
					});
					$('.where1_create').blur(function () {
						obj.from.where1 = $(this).val();
					});

					$('.hour_create').blur(function () {
						obj.from.hour = $(this).val();
					});

					$('.minute_create').blur(function () {
						obj.from.minute = $(this).val();
					});

					$('.save_create').blur(function () {
						obj.from.save = $(this).val();
					});

					$('.sBody_create').blur(function () {
						obj.from.sbody = $(this).val();
					});
					$('.url_create').blur(function () {
						obj.from.urladdress = $(this).val();
					});

					$('[aria-labelledby="cycle"] a').unbind().click(function () {
						$('.cycle_btn').find('b').attr('val',$(this).attr('value')).html($(this).html());
						var type = $(this).attr('value');
						switch(type){
							case 'day':
								$('.week_btn').hide();
								$('.where1_input').hide();
								$('.hour_input').show().find('input').val('1');
								$('.minute_input').show().find('input').val('30');
								obj.from.week = '';
								obj.from.type = '';
								obj.from.hour = 1;
								obj.from.minute = 30;
							break;
							case 'day-n':
								$('.week_btn').hide();
								$('.where1_input').show().find('input').val('1');
								$('.hour_input').show().find('input').val('1');
								$('.minute_input').show().find('input').val('30');
								obj.from.week = '';
								obj.from.where1 = 1;
								obj.from.hour = 1;
								obj.from.minute = 30;
							break;
							case 'hour':
								$('.week_btn').hide();
								$('.where1_input').hide();
								$('.hour_input').hide();
								$('.minute_input').show().find('input').val('30');
								obj.from.week = '';
								obj.from.where1 = '';
								obj.from.hour = '';
								obj.from.minute = 30;
							break;
							case 'hour-n':
								$('.week_btn').hide();
								$('.where1_input').hide();
								$('.hour_input').show().find('input').val('1');
								$('.minute_input').show().find('input').val('30');
								obj.from.week = '';
								obj.from.where1 = '';
								obj.from.hour = 1;
								obj.from.minute = 30;
							break;
							case 'minute-n':
								$('.week_btn').hide();
								$('.where1_input').hide();
								$('.hour_input').hide();
								$('.minute_input').show();
								obj.from.week = '';
								obj.from.where1 = '';
								obj.from.hour = '';
								obj.from.minute = 30;
								console.log(obj.from);
							break;
							case 'week':
								$('.week_btn').show();
								$('.where1_input').hide();
								$('.hour_input').show();
								$('.minute_input').show();
								obj.from.week = 1;
								obj.from.where1 = '';
								obj.from.hour = 1;
								obj.from.minute = 30;
							break;
							case 'month':
								$('.week_btn').hide();
								$('.where1_input').show();
								$('.hour_input').show();
								$('.minute_input').show();
								obj.from.week = '';
								obj.from.where1 = 1;
								obj.from.hour = 1;
								obj.from.minute = 30;
							break;
						}
						obj.from.type = $(this).attr('value');
					});

					$('[aria-labelledby="week"] a').unbind().click(function () {
						$('.week_btn').find('b').attr('val',$(this).attr('value')).html($(this).html());
						obj.from.week = $(this).attr('value');
					});

					$('[aria-labelledby="backupTo"] a').unbind().click(function () {
						$('.backup_btn').find('b').attr('val',$(this).attr('value')).html($(this).html());
						obj.from.backup_to = $(this).attr('value');
					});
					$('.plan-submits').unbind().click(function(){
						if(obj.from.type == 'hour-n'){
							obj.from.where1 = obj.from.hour;
							obj.from.hour = '';
						} else if(obj.from.type == 'minute-n') {
							obj.from.where1 = obj.from.minute;
							obj.from.minute = '';
						}
						var loadT = layer.msg('Saving edits, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
						$.post('/crontab/modify_crond',obj.from,function(rdata){

							if (!rdata.status){
								layer.msg(rdata.msg,{icon:rdata.status?1:2});
								return;
							}

							showMsg(rdata.msg, function(){
								layer.closeAll();
								getCronData(1);
								initDropdownMenu();
							},{icon:rdata.status?1:2}, 2000);

						},'json');
					});
				}
				,cancel: function(){
				    initDropdownMenu();
				}
			});
		});
	},'json');
}


function getselectname(){
	$(".dropdown ul li a").click(function(){
		var txt = $(this).text();
		var type = $(this).attr("value");
		$(this).parents(".dropdown").find("button b").text(txt).attr("val",type);
	});
}

function closeOpt(){
	$("#ptime").html('');
}

function toWeek(){
	var mBody = '<div class="dropdown planweek pull-left mr20">\
				  <button class="btn btn-default dropdown-toggle" type="button" id="excode_week" data-toggle="dropdown">\
					<b val="1">Monday</b> <span class="caret"></span>\
				  </button>\
				  <ul class="dropdown-menu" role="menu" aria-labelledby="excode_week">\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="1">Monday</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="2">Tuesday</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="3">Wednesday</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="4">Thursday</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="5">Friday</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="6">Saturday</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="0">Sunday</a></li>\
				  </ul>\
				</div>';
	$("#ptime").html(mBody);
	getselectname();
}

function toWhere1(ix){
	var mBody ='<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="where1" value="3" maxlength="2" max="31" min="0"></span>\
					<span class="name">'+ix+'</span>\
				</div>';
	$("#ptime").append(mBody);
}

function toHour(){
	var mBody = '<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="hour" value="1" maxlength="2" max="23" min="0"></span>\
					<span class="name">Hour</span>\
					</div>';
	$("#ptime").append(mBody);
}

function toMinute(){
	var mBody = '<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="minute" value="30" maxlength="2" max="59" min="0"></span>\
					<span class="name">Minute</span>\
					</div>';
	$("#ptime").append(mBody);

}

function toFile(){
	var tBody = '<input type="text" value="" name="file" id="viewfile" onclick="fileupload()" readonly="true">\
				<button class="btn btn-default" onclick="fileupload()">Last time</button>';
	$("#implement").html(tBody);
	$(".planname input[name='name']").removeAttr('readonly style').val("");
}

function toShell(){
	var tBody = "<textarea class='txtsjs bt-input-text' name='sBody'></textarea>";
	$("#implement").html(tBody);
	$(".planname input[name='name']").removeAttr('readonly style').val("");
}

function toUrl(){
	var tBody = "<input type='text' style='width:400px; height:34px' class='bt-input-text' name='urladdress' id='urladdress' placeholder='"+lan.crontab.url_address+"' value='http://' />";
	$("#implement").html(tBody);
	$(".planname input[name='name']").removeAttr('readonly style').val("");
}

function rememory(){
	$(".planname input[name='name']").removeAttr('readonly style').val("");
	$(".planname input[name='name']").val(lan.crontab.mem);
	$("#implement").html(lan.crontab.mem_ps);
	return;
}

function fileupload(){
	$("#sFile").change(function(){
		$("#viewfile").val($("#sFile").val());
	});
	$("#sFile").click();
}

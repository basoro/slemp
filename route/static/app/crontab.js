function isURL(str_url){
	var strRegex = '^(https|http|ftp|rtsp|mms)?://.+';
	var re=new RegExp(strRegex);
	if (re.test(str_url)){
		return (true);
	}else{
		return (false);
	}
}

var num = 0;

function getLogs(id){
	layer.msg('Mengambil data, harap tunggu...',{icon:16,time:0,shade: [0.3, '#000']});
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
			closeBtn:2,
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
				'<span class="btOpen" onclick="setTaskStatus(' + rdata.data[i].id + ',0)" style="color:rgb(92, 184, 92);cursor:pointer" title="Disable this scheduled task">Active<span class="glyphicon glyphicon-play"></span></span>'
				:'<span onclick="setTaskStatus('+ rdata.data[i].id +',1)" class="btClose" style="color:red;cursor:pointer" title="Enable this scheduled task">Deactive<span style="color:rgb(255, 0, 0);" class="glyphicon glyphicon-pause"></span></span>';

				cbody += "<tr>\
							<td><input type='checkbox' onclick='checkSelect();' title='"+rdata.data[i].name+"' name='id' value='"+rdata.data[i].id+"'></td>\
							<td>"+rdata.data[i].name+"</td>\
							<td>"+status+"</td>\
							<td>"+rdata.data[i].type+"</td>\
							<td>"+rdata.data[i].cycle+"</td>\
							<td>-</td>\
							<td>--</td>\
							<td>"+rdata.data[i].addtime+"</td>\
							<td>\
								<a href=\"javascript:startTask("+rdata.data[i].id+");\" class='btlink'>Exe</a> | \
								<a href=\"javascript:editTaskInfo('"+rdata.data[i].id+"');\" class='btlink'>Edit</a> | \
								<a href=\"javascript:getLogs("+rdata.data[i].id+");\" class='btlink'>Log</a> | \
								<a href=\"javascript:planDel("+rdata.data[i].id+" ,'"+rdata.data[i].name.replace('\\','\\\\').replace("'","\\'").replace('"','')+"');\" class='btlink'>Del</a>\
							</td>\
						</tr>";
			}
		}
		$('#cronbody').html(cbody);
		$('#softPage').html(rdata.list)
	},'json');
}

function setTaskStatus(id,status){
	var confirm = layer.confirm(status == '0'?'After a scheduled task is suspended, it will not continue to run. Do you really want to deactivate this scheduled task?':'The scheduled task is disabled, do you want to enable this scheduled task', {title:'Hint',icon:3,closeBtn:2,btn:['Yes','No']},function(index) {
		if (index > 0) {
			var loadT = layer.msg('Setting status, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
			$.post('/crontab/set_cron_status',{id:id},function(rdata){
				layer.closeAll();
				layer.close(confirm);
				layer.msg(rdata.data,{icon:rdata.status?1:2});
				if(rdata.status) {
					getCronData(1);
				}
			},'json');
		}
	});
}

function startTask(id){
	layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	var data='id='+id;
	$.post('/crontab/start_task',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

function closeLogs(id){
	layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	var data='id='+id;
	$.post('/crontab/del_logs',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

function planDel(id,name){
	safeMessage(lan.get('del',[name]),'Are you sure you want to delete this task?',function(){
		var load = layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
		var data='id='+id;
		$.post('/crontab/del',data,function(rdata){
			layer.close(load);
			showMsg(rdata.msg, function(){
				getCronData(1);
			},{icon:rdata.status?1:2,time:2000});
		},'json');
	});
}

function allDeleteCron(){
	var checkList = $("input[name=id]");
	var dataList = new Array();
	for(var i=0;i<checkList.length;i++){
		if(!checkList[i].checked) continue;
		var tmp = new Object();
		tmp.name = checkList[i].title;
		tmp.id = checkList[i].value;
		dataList.push(tmp);
	}
	safeMessage('Batch delete tasks!',"<a style='color:red;'>"+lan.get('del_all_task',[dataList.length])+"</a>",function(){
		layer.closeAll();
		syncDeleteCron(dataList,0,'');
	});
}

function syncDeleteCron(dataList,successCount,errorMsg){
	if(dataList.length < 1) {
		layer.msg(lan.get('del_all_task_ok',[successCount]),{icon:1});
		return;
	}
	var loadT = layer.msg(lan.get('del_all_task_the',[dataList[0].name]),{icon:16,time:0,shade: [0.3, '#000']});
	$.ajax({
			type:'POST',
			url:'/crontab?action=DelCrontab',
			data:'id='+dataList[0].id+'&name='+dataList[0].name,
			async: true,
			success:function(frdata){
				layer.close(loadT);
				if(frdata.status){
					successCount++;
					$("input[title='"+dataList[0].name+"']").parents("tr").remove();
				}else{
					if(!errorMsg){
						errorMsg = '<br><p>'+lan.crontab.del_task_err+'</p>';
					}
					errorMsg += '<li>'+dataList[0].name+' -> '+frdata.msg+'</li>'
				}

				dataList.splice(0,1);
				syncDeleteCron(dataList,successCount,errorMsg);
			}
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

	var where1 = $("#ptime input[name='where1']").val();
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

	if(where1 > is1 || where1 < is2){
		$("#ptime input[name='where1']").focus();
		layer.msg('The form is invalid, please re-enter!',{icon:2});
		return;
	}

	where1 = $('#excode_week b').attr('val');
	$("#set-Config input[name='where1']").val(where1);

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
		layer.msg('Invalid minute value!',{icon:2});
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

	if(sType == 'toFile'){
		if($("#viewfile").val() == ''){
			layer.msg('Please select a script file!',{icon:2});
			return;
		}
	} else {
		if(sBody == ''){
			$("#implement textarea[name='sBody']").focus();
			layer.msg('Script code cannot be empty!',{icon:2});
			return;
		}
	}

	var urladdress = $("#urladdress").val();
	if(sType == 'toUrl'){
		if(!isURL(urladdress)){
			layer.msg('Incorrect URL address!',{icon:2});
			$("implement textarea[name='urladdress']").focus();
			return;
		}
	}
	// urladdress = encodeURIComponent(urladdress);
	$("#set-Config input[name='urladdress']").val(urladdress);
	$("#set-Config input[name='sType']").val(sType);
	$("#set-Config textarea[name='sBody']").val(decodeURIComponent(sBody));

	if(sType == 'site' || sType == 'database'){
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

	$("#set-Config input[name='sName']").val(sName);
	layer.msg('Adding, please wait...!',{icon:16,time:0,shade: [0.3, '#000']});
	var data = $("#set-Config").serialize() + '&sBody='+sBody + '&urladdress=' + urladdress;
	console.log(data);
	$.post('/crontab/add',data,function(rdata){
		if(!rdata.status) {
			layer.msg(rdata.msg,{icon:2, time:2000});
			return;
		}
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		getCronData(1);
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
				toWhere1('Hari');
				toHour();
				toMinute();
				break;
			case 'hour':
				closeOpt();
				toMinute();
				break;
			case 'hour-n':
				closeOpt();
				toWhere1('Jam');
				toMinute();
				break;
			case 'minute-n':
				closeOpt();
				toWhere1('Menit');
				break;
			case 'week':
				closeOpt();
				toWeek();
				toHour();
				toMinute();
				break;
			case 'month':
				closeOpt();
				toWhere1('Hari');
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
				$(".controls").html('Free Memory');
				break;
			case 'site':
				toBackup('sites');
				$(".controls").html('Backup website');
				break;
			case 'database':
				toBackup('databases');
				$(".controls").html('Backup database');
				break;
			case 'logs':
				toBackup('logs');
				$(".controls").html('Cut Log');
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
			sMsg = 'Backup website';
			sType = "sites";
			break;
		case 'databases':
			sMsg = 'Backup database';
			sType = "databases";
			break;
		case 'logs':
			sMsg = 'Cut log';
			sType = "sites";
			break;
	}
	var data='type='+sType
	$.post('/crontab/get_data_list',data,function(rdata){
		$(".planname input[name='name']").attr('readonly','true').css({"background-color":"#f6f6f6","color":"#666"});
		var sOpt = "";
		if(rdata.data.length == 0){
			layer.msg(lan.public.list_empty,{icon:2})
			return
		}
		for(var i=0;i<rdata.data.length;i++){
			if(i==0){
				$(".planname input[name='name']").val(sMsg+'['+rdata.data[i].name+']');
			}
			sOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.data[i].name+'">'+rdata.data[i].name+'['+rdata.data[i].ps+']</a></li>';
		}

		var orderOpt = '';
		for (var i=0;i<rdata.orderOpt.length;i++){
			orderOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.orderOpt[i].name+'">'+rdata.orderOpt[i].title+'</a></li>'
		}


		var sBody = '<div class="dropdown pull-left mr20">\
					  <button class="btn btn-default dropdown-toggle" type="button" id="backdata" data-toggle="dropdown" style="width:auto">\
						<b id="sName" val="'+rdata.data[0].name+'">'+rdata.data[0].name+'['+rdata.data[0].ps+']</b> <span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="backdata">\
					  	<li><a role="menuitem" tabindex="-1" href="javascript:;" value="backupAll">All</a></li>\
					  	'+sOpt+'\
					  </ul>\
					</div>\
					<div class="textname pull-left mr20">Backup to</div>\
					<div class="dropdown planBackupTo pull-left mr20">\
					  <button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:auto;">\
						<b val="localhost">Server disk</b> <span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="localhost">Server disk</a></li>\
						'+ orderOpt +'\
					  </ul>\
					</div>\
					<div class="textname pull-left mr20">keep</div><div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="save" id="save" value="3" maxlength="4" max="100" min="1"></span>\
					<span class="name">copy</span>\
					</div>';
		$("#implement").html(sBody);
		getselectname();
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
		// console.log('init:', rdata);
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
			sTypeArray:[['toShell','Shell script'],['site','Backup website'],['database','Backup database'],['logs','Log cutting'],['path','Backup directory'],['rememory','Free memory'],['toUrl','Access URL']],
			cycleArray:[['day','Harian'],['day-n','Hari ke'],['hour','Tiap Jam'],['hour-n','Jam ke'],['minute-n','Menit ke'],['week','Mingguan'],['month','Bulanan']],
			weekArray:[[1,'Senin'],[2,'Selasa'],[3,'Rabu'],[4,'Kamis'],[5,'Jum\'at'],[6,'Sabtu'],[7,'Minggu']],
			sNameArray:[],
			backupsArray:[],
			create:function(callback){
				for(var i = 0; i <obj['sTypeArray'].length; i++){
					if(obj.from['stype'] == obj['sTypeArray'][i][0]){
						sTypeName  = obj['sTypeArray'][i][1];
					}
					sTypeDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['sTypeArray'][i][0] +'">'+ obj['sTypeArray'][i][1] +'</a></li>';
				}

				for(var i = 0; i <obj['cycleArray'].length; i++){
					if(obj.from['type'] == obj['cycleArray'][i][0])  cycleName  = obj['cycleArray'][i][1];
					cycleDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['cycleArray'][i][0] +'">'+ obj['cycleArray'][i][1] +'</a></li>';
				}

				for(var i = 0; i <obj['weekArray'].length; i++){
					if(obj.from['week'] == obj['weekArray'][i][0])  weekName  = obj['weekArray'][i][1];
					weekDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['weekArray'][i][0] +'">'+ obj['weekArray'][i][1] +'</a></li>';
				}

				if(obj.from.stype == 'site' || obj.from.stype == 'database' || obj.from.stype == 'path' || obj.from.stype == 'logs'){
					$.post('/crontab/get_data_list',{type:obj.from.stype  == 'databases'?'database':'sites'},function(rdata){
						obj.sNameArray = rdata.data;
						obj.sNameArray.unshift({name:'ALL',ps:'All'});
						obj.backupsArray = rdata.orderOpt;
						obj.backupsArray.unshift({title:'Server disk',value:'localhost'});
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
			layer.open({
				type:1,
				title:'Edit scheduled tasks ['+rdata.name+']',
				area: ['850px','450px'],
				skin:'layer-create-content',
				shadeClose:false,
				closeBtn:2,
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
									<div class="plan_hms pull-left mr20 bt-input-text hour_input" style="display:'+ (obj.from.type == "day" || obj.from.type == 'day-n' || obj.from.type == 'hour-n' || obj.from.type == 'week' || obj.from.type == 'month'?'block;':'none') +'"><span><input type="number" name="hour" class="hour_create" value="'+ ( obj.from.type == 'hour-n' ? obj.from.where1 : obj.from.hour ) +'" maxlength="2" max="23" min="0"></span> <span class="name">Time</span> </div>\
									<div class="plan_hms pull-left mr20 bt-input-text minute_input"><span><input type="number" name="minute" class="minute_create" value="'+ (obj.from.type == 'minute-n' ? obj.from.where1 : obj.from.minute)+'" maxlength="2" max="59" min="0"></span> <span class="name">Minute</span> </div>\
								</div>\
							</div>\
							<div class="clearfix plan ptb10 site_list" style="display:none">\
								<span class="typename controls c4 pull-left f14 text-right mr20">'+ sTypeName  +'</span>\
								<div style="line-height:34px"><div class="dropdown pull-left mr20 sName_btn" style="display:'+ (obj.from.sType != "path"?'block;':'none') +'">\
									<button class="btn btn-default dropdown-toggle" type="button"  data-toggle="dropdown" style="width:auto" disabled="disabled">\
										<b id="sName" val="'+ obj.from.sname +'">'+ obj.from.sname +'</b>\
										<span class="caret"></span>\
									</button>\
									<ul class="dropdown-menu" role="menu" aria-labelledby="sName">'+ sNameDom +'</ul>\
								</div>\
								<div class="info-r" style="float: left;margin-right: 25px;display:'+ (obj.from.sType == "path"?'block;':'none') +'">\
									<input id="inputPath" class="bt-input-text mr5 " type="text" name="path" value="'+ obj.from.sName +'" placeholder="Backup directory" style="width:208px;height:33px;" disabled="disabled">\
								</div>\
								<div class="textname pull-left mr20">Backup to</div>\
									<div class="dropdown  pull-left mr20">\
										<button class="btn btn-default dropdown-toggle backup_btn" type="button"  data-toggle="dropdown" style="width:auto;">\
											<b val="'+ obj.from.backup_to +'">'+ backupsName +'</b>\
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="backupTo">'+ backupsDom +'</ul>\
									</div>\
									<div class="textname pull-left mr20">keep</div>\
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
								<div style="line-height:34px">Release the memory usage of PHP, MYSQL and OpenResty. It is recommended to execute it in the middle of the night every day!</div>\
							</div>\
							<div class="clearfix plan ptb10" style="display:'+ (obj.from.stype == "toUrl"?'block;':'none') +'">\
								<span class="typename controls c4 pull-left f14 text-right mr20">URL address</span>\
								<div style="line-height:34px"><input type="text" style="width:400px; height:34px" class="bt-input-text url_create" name="urladdress"  placeholder="URL address" value="'+ obj.from.urladdress +'"></div>\
							</div>\
							<div class="clearfix plan ptb10">\
								<div class="bt-submit plan-submits " style="margin-left: 141px;">Save</div>\
							</div>\
						</div>'
				,cancel: function(){
				    initDropdownMenu();
				}
			});
			setTimeout(function(){
				if(obj.from.stype == 'toShell'){
					$('.site_list').hide();
				}else if(obj.from.stype == 'rememory'){
					$('.site_list').hide();
				}else if( obj.from.stype == 'toUrl'){
					$('.site_list').hide();
				}else{
					$('.site_list').show();
				}

				obj.from.minute = $('.minute_create').val();

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
					layer.msg('Saving edits, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
					$.post('/crontab/modify_crond',obj.from,function(rdata){
						layer.closeAll();
						getCronData(1);
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
						initDropdownMenu();
					},'json');
				});
			},100);
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
					<b val="1">Senin</b> <span class="caret"></span>\
				  </button>\
				  <ul class="dropdown-menu" role="menu" aria-labelledby="excode_week">\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="1">Senin</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="2">Selasa</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="3">Rabu</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="4">Kamis</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="5">Jum\'at</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="6">Sabtu</a></li>\
					<li><a role="menuitem" tabindex="-1" href="javascript:;" value="0">Minggu</a></li>\
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
					<span class="name">Jam</span>\
					</div>';
	$("#ptime").append(mBody);
}

function toMinute(){
	var mBody = '<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="minute" value="30" maxlength="2" max="59" min="0"></span>\
					<span class="name">Menit</span>\
					</div>';
	$("#ptime").append(mBody);

}

function toFile(){
	var tBody = '<input type="text" value="" name="file" id="viewfile" onclick="fileupload()" readonly="true">\
				<button class="btn btn-default" onclick="fileupload()">Upload</button>';
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

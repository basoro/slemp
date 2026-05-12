
function gdPost(method,args,callback){
    var _args = null; 
    if (typeof(args) == 'string'){
        _args = JSON.stringify(toArrayObject(args));
    } else {
        _args = JSON.stringify(args);
    }

    var loadT = layer.msg('Sedang mengambil...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'gdrive', func:method, args:_args}, function(data) {
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


function createDir(){
    layer.open({
        type: 1,
        area: "400px",
        title: "Buat direktori",
        closeBtn: 1,
        shift: 5,
        shadeClose: false,
        btn: ['OK','Batal'],
        content:'<div class="bingfa bt-form c6" style="padding-bottom: 10px;">\
                    <p>\
                        <span class="span_tit">Nama direktori: </span>\
                        <input style="width: 200px;" type="text" name="newPath" value="">\
                    </p>\
                </div>',
        success:function(){
            $("input[name='newPath']").focus().keyup(function(e){
                if(e.keyCode == 13) $(".layui-layer-btn0").click();
            });
        },
        yes:function(index,layero){
            var name = $("input[name='newPath']").val();
            if(name == ''){
                layer.msg('Nama direktori tidak boleh kosong!',{icon:2});
                return;
            }
            var parents = $("#myPath").val();
            var cur_file_id = $('#curPath').val();
            if (cur_file_id!=''){
                parents = cur_file_id;
            }

            var dirname = name;
            var loadT = layer.msg('Sedang membuat direktori['+dirname+']...',{icon:16,time:0,shade: [0.3, '#000']});
            gdPost('create_dir', {parents:parents,name:dirname}, function(data){
            	layer.close(loadT);
                var rdata = $.parseJSON(data.data);
                if(rdata.status) {
                    showMsg(rdata.msg, function(){
                        layer.close(index);
                        var file_id = $('#myPath').val();
                        if (cur_file_id!=''){
                            file_id = cur_file_id;
                        }
                        gdList(file_id);
                    } ,{icon:1}, 2000);
                } else{
                    layer.msg(rdata.msg,{icon:2});
                }
            });
        }
    });
}


//PengaturanAPI
function authApi(){

    gdPost('conf', {}, function(rdata){
        var rdata = $.parseJSON(rdata.data);

        // console.log(rdata);
        // console.log(rdata.data.auth_url);
        var apicon = '';
        if (rdata.status){

		    var html = '';
		    html += '<button id="clear_auth" onclick="clearAuth();" class="btn btn-default btn-sm">Hapus Konfigurasi</button>';
		
		    var loadOpen = layer.open({
		        type: 1,
		        title: 'Sudah Diotorisasi',
		        area: '240px',
		        content:'<div class="change-default pd20">'+html+'</div>',
		        success: function(){
		        	$('#clear_auth').click(function(){
		        		gdPost('clear_auth', {}, function(rdata){
							var rdata = $.parseJSON(rdata.data);
							showMsg(rdata.msg,function(){
								layer.close(loadOpen);
					            gdList('');
					        },{icon:rdata.status?1:2},2000);
						});  
		        	});	
		        }
		    });
		    return true;

        } else{
	        apicon = '<div class="new_form">'+$("#check_api").html()+'</div>';
        }
        
        var layer_auth = layer.open({
            type: 1,
            area: "620px",
            title: "Otorisasi Google Drive",
            closeBtn: 1,
            shift: 5,
            shadeClose: false,
            content:apicon,
            success:function(layero,index){
            	// console.log(layero,index);
            	if (!rdata.status){
            		layero.find('.step_two_url').val(rdata.data['auth_url']);
            		layero.find('.open_btlink').attr('href',rdata.data['auth_url']);

            		layero.find('.ico-copy').click(function(){
            			copyPass(rdata.data['auth_url']);
            		});

            		layero.find('.set_auth_btn').click(function(){

            			var url = layero.find('.google_drive').val();
						if ( url == ''){
							layer.msg("URL verifikasi tidak boleh kosong",{icon:2});
							return;
						}
						// console.log(url);
						gdPost('set_auth_url', {url:url}, function(rdata){
							var rdata = $.parseJSON(rdata.data);
							var show_time = 2000;
							if (!rdata.status){
								show_time = 10000;
							}

							showMsg(rdata.msg,function(){
								if (rdata.status){
									layer.close(layer_auth);
									gdList('');
								}
					        },{icon:rdata.status?1:2},show_time);
						});
            		});


            	}
            	
            }
        });
    });
}

//Hitung pergeseran direktori saat ini
function upPathLeft(){
    var UlWidth = $(".place-input ul").width();
    var SpanPathWidth = $(".place-input").width() - 20;
    var Ml = UlWidth - SpanPathWidth;
    if(UlWidth > SpanPathWidth ){
        $(".place-input ul").css("left",-Ml)
    }
    else{
        $(".place-input ul").css("left",0)
    }
}

function getGDTime(a) {
    return new Date(a).format("yyyy/MM/dd hh:mm:ss")
}

function gdList(file_id){
    $('#curPath').val(file_id);
    gdPost('get_list', {file_id:file_id}, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        console.log(rdata);
        if(rdata.status === false){
            showMsg(rdata.msg,function(){
                authApi();
            },{icon:2});
            return;
        }

        var mlist = rdata.data;
        var listBody = '';
        var listFiles = '';
        for(var i=0;i<mlist.length;i++){
            if(mlist[i].size == null){
                listFiles += '<tr><td class="cursor" onclick="gdList(\''+(mlist[i].id).replace('//','/')+'\')"><span class="ico ico-folder"></span>\<span>'+mlist[i].name+'</span></td>\
                <td>-</td>\
                <td>-</td>\
                <td class="text-right"><a class="btlink" onclick="deleteFile(\''+mlist[i].id+'\', true)">Hapus</a></td></tr>'
            }else{
                listFiles += '<tr><td class="cursor"><span class="ico ico-file"></span><span>'+mlist[i].name+'</span></td>\
                <td>'+toSize(mlist[i].size)+'</td>\
                <td>'+getGDTime(mlist[i].createdTime)+'</td>\
                <td class="text-right"><a target="_blank" href="'+mlist[i].webViewLink+'" class="btlink">Unduh</a> | <a class="btlink" onclick="deleteFile(\''+mlist[i].name+'\', false)">Hapus</a></td></tr>'
            }
        }
        listBody += listFiles;
        var pathLi = '<li><a title="Direktori Utama" onclick="gdList(\'\')">Direktori Utama</a></li>';
        
        if (mlist.length>0){
            $('#myPath').val(mlist[0]['parents'][0]);
        }
        
        $(".upyunCon .place-input ul").html(pathLi);
        $(".upyunlist .list-list").html(listBody);

        $('#backBtn').unbind().click(function() {
            gdList('');
        });

        $('.upyunCon .refreshBtn').unbind().click(function(){
            var file_id = $('#myPath').val();
            gdList(file_id);
        });
    });
}


//Hapus file
function deleteFile(name, is_dir){
    if (is_dir === false){
        safeMessage('Hapus file','Setelah dihapus tidak dapat dipulihkan, yakin ingin menghapus['+name+']?',function(){
            var path = $("#myPath").val();
            var filename = name;
            gdPost('delete_file', {filename:filename,path:path}, function(rdata){
                var rdata = $.parseJSON(rdata.data);
                showMsg(rdata.msg,function(){
                    var file_id = $('#myPath').val();
                    gdList(file_id);
                },{icon:rdata.status?1:2},2000);
            });
        });
    } else {
        safeMessage('Hapus folder','Setelah dihapus tidak dapat dipulihkan, yakin ingin menghapussumber daya file['+name+']?',function(){
            var path = $("#myPath").val();
            gdPost('delete_dir', {dir_name:name,path:path}, function(rdata){
                var rdata = $.parseJSON(rdata.data);
                showMsg(rdata.msg,function(){
                    var file_id = $('#myPath').val();
                    gdList(file_id);
                },{icon:rdata.status?1:2},2000);
            });
        });
    }
}
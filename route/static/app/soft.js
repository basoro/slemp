function resetPluginWinWidth(width){
    $("div[id^='layui-layer'][class*='layui-layer-page']").width(width);
}

function resetPluginWinHeight(height){
    $("div[id^='layui-layer'][class*='layui-layer-page']").height(height);
    $(".bt-form .bt-w-main").height(height-42);
}

function softMain(name, title, version) {

    var _title = title.replace('-'+version,'')

    var loadT = layer.msg("Lagi diproses, tunggu bentar...", { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/plugins/setting?name='+name, function(rdata) {
        layer.close(loadT);
        layer.open({
            type: 1,
            area: '640px',
            title: _title + '[' + version + "] manajemen",
            closeBtn: 1,
            shift: 0,
            content: rdata
        });
        $(".bt-w-menu p").click(function() {
            $(this).addClass("bgw").siblings().removeClass("bgw");
        });

        //version to
        $(".plugin_version").attr('version',version).hide();
    });
}

function getSList(isdisplay) {
    if (isdisplay !== true) {
        var loadT = layer.msg('Lagi ambil daftar...', { icon: 16, time: 0, shade: [0.3, '#000'] })
    }
    if (!isdisplay || isdisplay === true)
        isdisplay = getCookie('p' + getCookie('soft_type'));
    if (isdisplay == true || isdisplay == 'true') isdisplay = 1;

    var search = $("#SearchValue").val();
    if (search != '') {
        search = '&search=' + search;
    }
    var type = '';
    var istype = getCookie('soft_type');
    if (istype == 'undefined' || istype == 'null' || !istype) {
        istype = '0';
    }

    type = '&type=' + istype;
    var page = '';
    if (isdisplay) {
        page = '&p=' + isdisplay;
        setCookie('p' + getCookie('soft_type'), isdisplay);
    }

    var condition = (search + type + page).slice(1);
    $.get('/plugins/list?' + condition, '', function(rdata) {
        layer.close(loadT);
        var tBody = '';
        var sBody = '';
        var pBody = '';

        for (var i = 0; i < rdata.type.length; i++) {
            var c = '';
            if (istype == rdata.type[i].type) {
                c = 'class="on"';
            }
            tBody += '<span typeid="' + rdata.type[i].type + '" ' + c + '>' + rdata.type[i].title + '</span>';
        }

        $(".softtype").html(tBody);
        $("#softPage").html(rdata.list);
        $("#softPage .Pcount").css({ "position": "absolute", "left": "0" })

        $(".task").text(rdata.data[rdata.length - 1]);
        for (var i = 0; i < rdata.data.length; i++) {
            var plugin = rdata.data[i];
            var len = plugin.versions.length;
            var version_info = '';
            var version = '';
            var softPath = '';
            var titleClick = '';
            var state = '';
            var indexshow = '';
            var checked = '';

            checked = plugin.display ? 'checked' : '';

            if (typeof plugin.versions == "string"){
                version_info += plugin.versions + '|';
            } else {
                for (var j = 0; j < len; j++) {
                    version_info += plugin.versions[j] + '|';
                }
            }
            if (version_info != '') {
                version_info = version_info.substring(0, version_info.length - 1);
            }


            var handle = '<a class="btlink" onclick="addVersion(\'' + plugin.name + '\',\'' + version_info + '\',\'' + plugin.tip + '\',this,\'' + plugin.title + '\',' + plugin.install_pre_inspection + ')">Pasang</a>';

            if (plugin.setup == true) {

                var mupdate = '';//(plugin.versions[n] == plugin.updates[n]) '' : '<a class="btlink" onclick="softUpdate(\'' + plugin.name + '\',\'' + plugin.versions[n].version + '\',\'' + plugin.updates[n] + '\')">Renew</a> | ';
                // if (plugin.versions[n] == '') mupdate = '';
                handle = mupdate + '<a class="btlink" onclick="softMain(\'' + plugin.name + '\',\'' + plugin.title + '\',\'' + plugin.setup_version + '\')">Atur</a> | <a class="btlink" onclick="uninstallVersion(\'' + plugin.name + '\',\'' + plugin.title +'\',\'' + plugin.setup_version + '\',' + plugin.uninstall_pre_inspection +')">Hapus</a>';
                titleClick = 'onclick="softMain(\'' + plugin.name + '\',\'' + plugin.title + '\',\'' + plugin.setup_version + '\')" style="cursor:pointer"';

                softPath = '<span class="glyphicon glyphicon-folder-open" title="' + plugin.path + '" onclick="openPath(\'' + plugin.path + '\')"></span>';
                if (plugin.coexist){
                    indexshow = '<div class="index-item"><input class="btswitch btswitch-ios" id="index_' + plugin.name  + plugin.versions + '" type="checkbox" ' + checked + '><label class="btswitch-btn" for="index_' + plugin.name + plugin.versions + '" onclick="toIndexDisplay(\'' + plugin.name + '\',\'' + plugin.versions + '\',\'' + plugin.coexist +'\')"></label></div>';
                } else {
                    indexshow = '<div class="index-item"><input class="btswitch btswitch-ios" id="index_' + plugin.name + '" type="checkbox" ' + checked + '><label class="btswitch-btn" for="index_' + plugin.name + '" onclick="toIndexDisplay(\'' + plugin.name + '\',\'' + plugin.setup_version + '\')"></label></div>';
                }

                if (plugin.status == true) {
                    state = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>'
                } else {
                    state = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
                }
            }

            if (plugin.task == '-2') {
                handle = '<a style="color:green;" href="javascript:task();">Lagi dihapus...</a>';
            } else if (plugin.task == '-1') {
                handle = '<a style="color:green;" href="javascript:task();">Lagi dipasang...</a>';
            } else if (plugin.task == '0') {
                handle = '<a style="color:#C0C0C0;" href="javascript:task();">Nunggu...</a>';
            }

            var plugin_title = plugin.title;
            if (plugin.setup && !plugin.coexist){
                plugin_title = plugin.title + ' ' + plugin.setup_version;
            }

            icon_link = "/plugins/file?name="+plugin.name+"&f=ico.png";
            if (plugin.icon != ''){
                icon_link = "/plugins/file?name="+plugin.name+"&f="+plugin.icon;
            }

            sBody += '<tr>' +
                '<td><span ' + titleClick + '>'+
                '<img data-src="'+icon_link+'" src="/static/img/loading.gif">' + plugin_title + '</span></td>' +
                '<td>' + plugin.ps + '</td>' +
                '<td>' + softPath + '</td>' +
                '<td>' + state + '</td>' +
                '<td>' + indexshow + '</td>' +
                '<td style="text-align: right;">' + handle + '</td>' +
                '</tr>';
        }

        sBody += pBody;


        $("#softList").html(sBody);
        $(".menu-sub span").click(function() {
            setCookie('soft_type', $(this).attr('typeid'));
            $(this).addClass("on").siblings().removeClass("on");
            getSList();
        });

        loadImage();
    },'json');
}

function installPreInspection(name, ver, callback){
    var loading = layer.msg('Lagi cek lingkungan instalasi...', { icon: 16, time: 0, shade: [0.3, '#000'] });
     $.post("/plugins/run", {'name':name,'version':ver,'func':'install_pre_inspection'}, function(rdata) {
        layer.close(loading);
        if (rdata.status){
            if (rdata.data == 'ok'){
                callback();
            } else {
                layer.msg(rdata.data, { icon: 2 });
            }
        } else {
            layer.msg(rdata.data, { icon: rdata.status ? 1 : 2 });
        }
    },'json');
}

function runInstall(data){
    var loadT = layer.msg('Lagi ditambahin ke installer...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post("/plugins/install", data, function(rdata) {
        layer.closeAll();
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        getSList();
    },'json');
}

function addVersion(name, ver, type, obj, title, install_pre_inspection) {
    var option = '';
    var titlename = title.replace("-"+ver,"");
    if (ver.indexOf('|') >= 0){
        var veropt = ver.split("|");
        var selectVersion = '';
        for (var i = 0; i < veropt.length; i++) {
            selectVersion += '<option>' + name + ' ' + veropt[i] + '</option>';
        }
        option = "<select id='selectVersion' class='bt-input-text' style='margin-left:30px'>" + selectVersion + "</select>";
    } else {
        option = '<span id="selectVersion" val="' + name + ' ' + ver + '"> [' + titlename + '] ' + ver + '</span>';
    }

    layer.open({
        type: 1,
        title: "["+titlename + "] Instalasi Perangkat Lunak",
        area: '350px',
        closeBtn: 1,
        shadeClose: true,
        btn: ['Kirim','Batal'],
        content: "<div class='bt-form pd20 c6'>\
			<div class='version line'>Versi terpasang：" + option + "</div>\
	    </div>",
        success:function(){
            $('.fangshi input').click(function() {
                $(this).attr('checked', 'checked').parent().siblings().find("input").removeAttr('checked');
            });
            installTips();
        },
        yes:function(index,layero){
            var info = $("#selectVersion").val().toLowerCase();
            if (info == ''){
                info = $("#selectVersion").attr('val').toLowerCase();
            }
            var info_split = info.split(' ');
            var name = info_split[0];
            var version = info_split[1];

            var type = $('.fangshi').prop("checked") ? '1' : '0';
            var request_args = "name=" + name + "&version=" + version + "&type=" + type;

            if (install_pre_inspection){
                installPreInspection(name, version, function(){
                    runInstall(request_args);
                    flySlow('layui-layer-btn0');
                });
                return;
            }

            runInstall(request_args);
            flySlow('layui-layer-btn0');
        }
    });
}

function uninstallPreInspection(name, title, ver, callback){
    var loading = layer.msg('Lagi cek lingkungan uninstal...', { icon: 16, time: 0, shade: [0.3, '#000'] });
     $.post("/plugins/run", {'name':name,'version':ver,'func':'uninstall_pre_inspection'}, function(rdata) {
        layer.close(loading);
        if (rdata.status){
            if (rdata.data == 'ok'){
                if (typeof(callback) == 'function'){
                    callback();
                }
            } else {
                layer.msg(rdata.data, { icon: 2 , time: 6666});
            }
        } else {
            layer.msg(rdata.data, { icon: rdata.status ? 1 : 2, time: 6666 });
        }
    },'json');
}


function runUninstallVersion(name, title, version){
    var title = title.replace("-"+version,"");
    layer.confirm(msgTpl('Beneran mau hapus [{1}-{2}]?', [title, version]), { icon: 3, closeBtn: 1 }, function() {
        var data = 'name=' + name + '&version=' + version;
        var loadT = layer.msg('Lagi diproses, tunggu bentar...', { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/plugins/uninstall', data, function(rdata) {
            layer.close(loadT)
            getSList();
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        },'json');
    });
}


function uninstallVersion(name, title, version, uninstall_pre_inspection) {
    if (uninstall_pre_inspection) {
        uninstallPreInspection(name,title,version,function(){
            runUninstallVersion(name,title,version);
        });
    } else {
        runUninstallVersion(name,title,version);
    }
}

function toIndexDisplay(name, version, coexist) {

    var status = $("#index_" + name).prop("checked") ? "0" : "1";
    if (coexist == "true") {
        var verinfo = version.replace(/\./, "");
        status = $("#index_" + name + verinfo).prop("checked") ? "0" : "1";
    }

    var data = "name=" + name + "&status=" + status + "&version=" + version;
    $.post("/plugins/set_index", data, function(rdata) {
        if (rdata.status) {
            layer.msg(rdata.msg, { icon: 1 })
        } else {
            layer.msg(rdata.msg, { icon: 2 })
        }
    },'json');
}

function indexListHtml(callback){


    // init
    $("#indexsoft").html('');
    var index_soft = '';
    for (var i = 0; i < 12; i++) {
        index_soft += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg"></div>';
    }
    $("#indexsoft").html(index_soft);

    $.get('/plugins/index_list', function(rdata) {
        // layer.close(loadT);
        $("#indexsoft").html('');
        var con = '';
        for (var i = 0; i < rdata.length; i++) {
            var plugin = rdata[i];
            var len = plugin.versions.length;
            var version_info = '';

            if (typeof plugin.versions == "string"){
                version_info += plugin.versions + '|';
            } else {
                for (var j = 0; j < len; j++) {
                    version_info += plugin.versions[j] + '|';
                }
            }
            if (version_info != '') {
                version_info = version_info.substring(0, version_info.length - 1);
            }

            if (plugin.status == true) {
                    state = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>'
                } else {
                    state = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
            }

            var name = plugin.title + ' ' + plugin.setup_version + '  ';
            var data_id = plugin.name + '-' + plugin.setup_version;
            if (plugin.coexist){
                name = plugin.title + '  ';
                data_id = plugin.name + '-' + plugin.versions;
            }

            con += '<div class="col-sm-3 col-md-3 col-lg-3" data-id="' + data_id + '">\
                <span class="spanmove"></span>\
                <div onclick="softMain(\'' + plugin.name + '\',\'' + plugin.title + '\',\'' + plugin.setup_version + '\')">\
                <div class="image"><img bk-src="/static/img/loading.gif" src="/plugins/file?name=' + plugin.name + '&f=ico.png" style="max-width:48px;"></div>\
                <div class="sname">' +  name + state + '</div>\
                </div>\
            </div>';

            // loadImage();
        }

        $("#indexsoft").html(con);
        var softboxlen = $("#indexsoft > div").length;
        var softboxsum = 12;
        var softboxcon = '';
        var softboxn = softboxlen;
        if (softboxlen <= softboxsum) {
            for (var i = 0; i < softboxsum - softboxlen; i++) {
                softboxcon += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg" data-id=""></div>';
            }
            $("#indexsoft").append(softboxcon);
        }

        if (typeof callback=='function'){
            callback();
        }
    },'json');
}

function indexSoft() {
    indexListHtml(function(){
        $("#indexsoft").dragsort({ dragSelector: ".spanmove", dragBetween: true, dragEnd: saveOrder, placeHolderTemplate: "<div class='col-sm-3 col-md-3 col-lg-3 dashed-border'></div>" });
    });

    function saveOrder() {
        var data = $("#indexsoft > div").map(function() { return $(this).attr("data-id"); }).get();
        tmp = [];
        for(i in data){
            // console.log(data[i]);
            if (data[i] != ''){
                tmp.push($.trim(data[i]));
            }
        }
        var ssort = tmp.join("|");
        $("input[name=list1SortOrder]").val(ssort);
        $.post("/plugins/index_sort", 'ssort=' + ssort, function(rdata) {
            if (!rdata.status){
                showMsg('Gagal diatur:'+ rdata.msg, function(){
                    indexListHtml();
                }, { icon: 16, time: 0, shade: [0.3, '#000'] });
            }
        },'json');
    };
}


function importPluginOpen(){
    $("#update_zip").on("change", function () {
        var files = $("#update_zip")[0].files;
        if (files.length == 0) {
            return;
        }
        importPlugin(files[0]);
        $("#update_zip").val('')
    });
    $("#update_zip").click();
}


function importPlugin(file){
    var formData = new FormData();
    formData.append("plugin_zip", file);
    $.ajax({
        url: "/plugins/update_zip",
        type: "POST",
        data: formData,
        processData: false,
        dataType:'json',
        contentType: false,
        success: function (data) {
            if (data.status === false) {
                layer.msg(data.msg, { icon: 2 });
                return;
            }
            var loadT = layer.open({
                type: 1,
                area: "500px",
                title: "Pasang paket plugin pihak ketiga",
                closeBtn: 1,
                shift: 5,
                shadeClose: false,
                content: '<style>\
                    .install_three_plugin{padding:25px;padding-bottom:70px}\
                    .plugin_user_info p { font-size: 14px;}\
                    .plugin_user_info {padding: 15px 30px;line-height: 26px;background: #f5f6fa;border-radius: 5px;border: 1px solid #efefef;}\
                    .btn-content{text-align: center;margin-top: 25px;}\
                </style>\
                <div class="bt-form c7  install_three_plugin pb70">\
                    <div class="plugin_user_info">\
                        <p><b>Nama：</b>'+ data.title + '</p>\
                        <p><b>Versi：</b>' + data.versions +'</p>\
                        <p><b>Catatan：</b>' + data.ps + '</p>\
                        <p><b>Ukuran：</b>' + toSize(data.size) + '</p>\
                        <p><b>Pembuat：</b>' + data.author + '</p>\
                        <p><b>Sumber：</b><a class="btlink" href="'+data.home+'" target="_blank">' + data.home + '</a></p>\
                    </div>\
                    <ul class="help-info-text c7">\
                        <li style="color:red;">Ini plugin pihak ketiga, keamanannya belum terjamin!</li>\
                        <li>Proses pasang butuh waktu beberapa menit, sabar ya!</li>\
                        <li>Kalau plugin ini udah ada, bakal ditimpa!</li>\
                    </ul>\
                    <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger mr5" onclick="layer.closeAll()">Batal</button><button type="button" class="btn btn-sm btn-success" onclick="importPluginInstall(\''+ data.name + '\',\'' + data.tmp_path +'\')">Pasang</button></div>\
                </div>'
            });

        },error: function (responseStr) {
            layer.msg('Upload failed 2!:' + responseStr, { icon: 2 });
        }
    });
}


function importPluginInstall(plugin_name, tmp_path) {
    layer.msg('Lagi dipasang, butuh waktu beberapa menit ya...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/plugins/input_zip', { plugin_name: plugin_name, tmp_path: tmp_path }, function (rdata) {
        layer.closeAll()
        if (rdata.status) {
            getSList(true);
        }
        setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }) }, 1000);
    },'json');
}

$(function() {
    if (window.document.location.pathname == '/soft/') {
        setInterval(function() { getSList(); }, 8000);
    }
});

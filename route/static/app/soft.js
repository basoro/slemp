function resetPluginWinWidth(width){
    $("div[id^='layui-layer'][class*='layui-layer-page']").width(width);
}

function resetPluginWinHeight(height){
    $("div[id^='layui-layer'][class*='layui-layer-page']").height(height);
    $(".bt-form .bt-w-main").height(height-42);
}

var phpUpdateInfo = {};

function renderPhpSecurityNotice(items) {
    var box = $('#phpSecurityNotice');
    if (!box.length) {
        return;
    }

    if (!items || items.length === 0) {
        box.hide().empty();
        return;
    }

    var list = '';
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if (item.eol && !item.target) {
            list += '<li style="margin-bottom:4px;">' + item.title +
                ': terpasang <b>' + item.installed + '</b> &mdash; sudah EOL dan tidak ada patch resmi. ' +
                'Migrasikan ke PHP 8.3 atau lebih baru.</li>';
            continue;
        }

        list += '<li style="margin-bottom:4px;">' + item.title +
            ': terpasang <b>' + item.installed + '</b>, patch <b>' + item.target + '</b>' +
            (item.patch ? ' (backport)' : '') + ' tersedia. ' +
            '<a class="btlink" onclick="softUpdate(\'' + item.name + '\',\'' + item.branch + '\',\'' + item.title + '\',\'' + item.installed + '\',\'' + item.target + '\')">Update sekarang</a></li>';
    }

    box.html('<div class="alert alert-warning" style="margin:0;">' +
        '<b>Peringatan keamanan PHP2Shell.</b> Branch PHP yang perlu ditindaklanjuti:' +
        '<ul style="margin:8px 0 0 18px;">' + list + '</ul>' +
        '</div>').show();
}

function pluginTaskText(plugin) {
    var label = (plugin.task_label || '').toLowerCase();
    if (label.indexOf('update') === 0) {
        return 'Lagi update...';
    }
    if (label.indexOf('uninstall') === 0 || label.indexOf('hapus') > -1) {
        return 'Lagi dihapus...';
    }
    return 'Lagi dipasang...';
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

function getSList() {
    var loadT = layer.msg('Lagi ambil daftar...', { icon: 16, time: 0, shade: [0.3, '#000'] })

    var search = $("#SearchValue").val();
    if (search != '') {
        search = '&search=' + search;
    }

    $.get('/plugins/list?limit=0' + search, '', function(rdata) {
        layer.close(loadT);
        var sBody = '';

        phpUpdateInfo = {};
        var phpSecurity = rdata.php_security || [];
        for (var s = 0; s < phpSecurity.length; s++) {
            phpUpdateInfo[phpSecurity[s].branch] = phpSecurity[s];
        }
        renderPhpSecurityNotice(phpSecurity);

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

                var updateLink = '';
                if (plugin.update_available) {
                    var updateTip = plugin.update_security ? plugin.update_security : ('Update ke ' + plugin.update_target);
                    updateLink = '<a class="btlink" style="color:#e6a23c" title="' + updateTip + '" onclick="softUpdate(\'' + plugin.name + '\',\'' + plugin.versions + '\',\'' + plugin.title + '\',\'' + plugin.installed_version + '\',\'' + plugin.update_target + '\')">Update</a> | ';
                }

                var mupdate = '';
                handle = updateLink + mupdate + '<a class="btlink" onclick="softMain(\'' + plugin.name + '\',\'' + plugin.title + '\',\'' + plugin.setup_version + '\')">Atur</a> | <a class="btlink" onclick="uninstallVersion(\'' + plugin.name + '\',\'' + plugin.title +'\',\'' + plugin.setup_version + '\',' + plugin.uninstall_pre_inspection +')">Hapus</a>';
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
                handle = '<a style="color:green;" href="javascript:task();">' + pluginTaskText(plugin) + '</a>';
            } else if (plugin.task == '0') {
                handle = '<a style="color:#C0C0C0;" href="javascript:task();">Nunggu...</a>';
            }

            var plugin_title = plugin.title;
            if (plugin.setup && !plugin.coexist){
                plugin_title = plugin.title + ' ' + plugin.setup_version;
            } else if (plugin.setup && plugin.coexist && plugin.installed_version){
                plugin_title = plugin.title + ' <span class="f12 c9">' + plugin.installed_version + '</span>';
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

        $("#softList").html(sBody);

        loadImage();
    },'json');
}

function softUpdate(name, version, title, installed, target) {
    var plugTitle = title.replace('-' + version, '');
    var updateInfo = phpUpdateInfo[version] || {};
    var changelog = updateInfo.changelog || [];
    var changelogHtml = '';
    var patchHtml = '';
    var targetLabel = 'Versi tersedia';

    if (updateInfo.patch) {
        targetLabel = 'Patch tersedia';
        patchHtml = '<p class="mb10" style="color:#e6a23c;"><b>Backport resmi:</b> nomor versi tetap ' + target + ', patch PHP2Shell diterapkan saat build.</p>';
    }

    if (changelog.length > 0) {
        changelogHtml = '<p class="mb10"><b>Changelog:</b></p>' +
            '<ul class="help-info-text c7">';
        for (var i = 0; i < changelog.length; i++) {
            changelogHtml += '<li>' + changelog[i] + '</li>';
        }
        changelogHtml += '</ul>';
    }

    layer.open({
        type: 1,
        area: '440px',
        title: 'Update ' + plugTitle + ' ' + version,
        closeBtn: 1,
        shadeClose: false,
        btn: ['Update', 'Batal'],
        content: '<div class="bt-form pd20 c6">\
            <p class="mb10">Versi terpasang: <b>' + installed + '</b></p>\
            <p class="mb10">' + targetLabel + ': <b>' + target + '</b></p>\
            ' + patchHtml + '\
            ' + changelogHtml + '\
            <ul class="help-info-text c7">\
                <li style="color:red;">Perbaikan keamanan PHP2Shell (CVE-2026-109618, CVE-2026-109619).</li>\
                <li>Proses build butuh 10-30 menit. PHP-FPM ' + version + ' akan restart dan situs sesaat menampilkan 502.</li>\
                <li>Konfigurasi php.ini dan pool PHP-FPM dipertahankan; backup otomatis dibuat sebelum update.</li>\
            </ul>\
        </div>',
        yes: function(index) {
            var loadT = layer.msg('Menambahkan tugas update...', { icon: 16, time: 0, shade: [0.3, '#000'] });
            $.post('/plugins/update', { name: name, version: version, target: target }, function(rdata) {
                layer.close(loadT);
                if (rdata.status) {
                    layer.close(index);
                    localStorage.setItem('open_task_box', '1');
                    setTimeout(function() {
                        task();
                        getSList();
                    }, 1000);
                } else {
                    layer.msg(rdata.msg, { icon: 2 });
                }
            }, 'json');
        }
    });
}

function installPreInspection(name, ver, callback){
    var loading = layer.msg('Lagi cek lingkungan instalasi...', { icon: 16, time: 0, shade: [0.3, '#000'] });
     $.post("/plugins/run", {'name':name,'version':ver,'func':'install_pre_inspection'}, function(rdata) {
        layer.close(loading);
        if (rdata.status){
            if (rdata.data == 'ok'){
                callback();
            } else {
                layer.alert(rdata.data, { icon: 2, title: 'Instalasi Gagal' });
            }
        } else {
            layer.alert(rdata.msg || rdata.data || 'Terjadi kesalahan sistem.', { icon: 2, title: 'Error' });
        }
     },'json');
}

function runInstall(data){
    var loadT = layer.msg('Lagi ditambahin ke installer...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post("/plugins/install", data, function(rdata) {
        layer.close(loadT);
        if (rdata.status) {
            localStorage.setItem('open_task_box', '1');
            flySlow('layui-layer-btn0');
        } else {
            layer.msg(rdata.msg, { icon: 2 });
        }
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
        end: function() {
            location.reload();
        },
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
                });
                return false;
            }

            runInstall(request_args);
            return false;
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
                layer.alert(rdata.data, { icon: 2, title: 'Uninstal Gagal' });
            }
        } else {
            layer.alert(rdata.msg || rdata.data || 'Terjadi kesalahan sistem.', { icon: 2, title: 'Error' });
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
            if (rdata.status) {
                setTimeout(function() {
                    task();
                }, 1000);
            }
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

$(function() {
    if (window.document.location.pathname == '/soft/' || window.document.location.pathname == '/soft') {

        if (localStorage.getItem('open_task_box') === '1') {
            localStorage.removeItem('open_task_box');
            task();
        }
    }
});

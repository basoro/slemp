$(function () {
    $(".mem-release").hover(function () {
        $(this).addClass("shine_green");
        if (!($(this).hasClass("mem-action"))) {
            $(this).find(".mem-re-min").hide();
            $(this).find(".mask").css({ "color": "#d2edd8" });
            $(this).find(".mem-re-con").css({ "display": "block" });
            $(this).find(".mem-re-con").animate({ "top": "0", opacity: 1 });
            $("#memory").text(lan.index.memre);
        }
    }, function () {
        $(this).removeClass("shine_green");
        $(this).find(".mask").css({ "color": "#20a53a" });
        $(this).find(".mem-re-con").css({ "top": "15px", opacity: 1, "display": "none" });
        $("#memory").text(getCookie("mem-before"));
        $(this).find(".mem-re-min").hide();
    }).click(function () {
        $(this).find(".mem-re-min").hide();
        if (!($(this).hasClass("mem-action"))) {
            $(this).addClass("mem-action mem-releasing");
            $(this).find(".mask").css({ "color": "#20a53a" });
            $(this).find(".mem-re-con").animate({ "top": "-400px", opacity: 0 });
            reMemory();
        }
    });
});

function getLoad(data) {
    $("#LoadList .mask").html("<span id='Load' style='font-size:14px'>Lagi ambil info..</span>");
    setCookie('one', data.one);
    setCookie('five', data.five);
    setCookie('fifteen', data.fifteen);
    var transformLeft, transformRight, LoadColor, Average, Occupy, AverageText, conterError = '';
    var index = $("#LoadList");
    if (Average == undefined) Average = data.one;
    setCookie('conterError', conterError);
    Occupy = Math.round((Average / data.max) * 100);
    if (Occupy > 100) Occupy = 100;
    if (Occupy <= 30) {
        LoadColor = '#20a53a';
        AverageText = 'Lancar jaya';
    } else if (Occupy <= 70) {
        LoadColor = '#6ea520';
        AverageText = 'Normal';
    } else if (Occupy <= 90) {
        LoadColor = '#ff9900';
        AverageText = 'Agak lambat';
    } else {
        LoadColor = '#dd2f00';
        AverageText = 'Macet';
    }
    index.find('.circle').css("background", LoadColor);
    index.find('.mask').css({ "color": LoadColor });
    $("#LoadList .mask").html("<span id='Load'></span>%");
    $('#Load').html(Occupy);
    $('#LoadState').html('<span>' + AverageText + '</span>');
    setImg();
}

$('#LoadList .circle').click(function () {
    getNet();
});

$('#LoadList .mask').hover(function () {
    var one, five, fifteen;
    var that = this;
    one = getCookie('one');
    five = getCookie('five');
    fifteen = getCookie('fifteen');
    var text = 'Rata-rata beban 1 menit terakhir: ' + one + '</br> Rata-rata beban 5 menit terakhir: ' + five + '</br> Rata-rata beban 15 menit terakhir: ' + fifteen + '';
    layer.tips(text, that, { time: 0, tips: [1, '#999'] });
}, function () {
    layer.closeAll('tips');
});


function showCpuTips(rdata) {
    $('#cpuChart .mask').unbind();
    $('#cpuChart .mask').hover(function () {
        var cpuText = '';

        if (rdata.cpu[2].length == 1) {
            var cpuUse = parseFloat(rdata.cpu[2][0] == 0 ? 0 : rdata.cpu[2][0]).toFixed(1);
            cpuText += 'CPU-1：' + cpuUse + '%'
        } else {
            for (var i = 1; i < rdata.cpu[2].length + 1; i++) {
                var cpuUse = parseFloat(rdata.cpu[2][i - 1] == 0 ? 0 : rdata.cpu[2][i - 1]).toFixed(1);
                if (i % 2 != 0) {
                    cpuText += 'CPU-' + i + '：' + cpuUse + '%&nbsp;|&nbsp;'
                } else {
                    cpuText += 'CPU-' + i + '：' + cpuUse + '%'
                    cpuText += '\n'
                }
            }
        }
        layer.tips(rdata.cpu[3] + "</br>" + rdata.cpu[5] + " CPU fisik, " + (rdata.cpu[4]) + " core fisik, " + rdata.cpu[1] + " core logis</br>" + cpuText, this, { time: 0, tips: [1, '#999'] });
    }, function () {
        layer.closeAll('tips');
    });
}



function reMemory() {
    setTimeout(function () {
        $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px' }).html('<span style="display:none">1</span>' + lan.index.memre_ok_0 + ' <img src="/static/img/ings.gif">');
        $.post('/system/rememory', '', function (rdata) {
            var percent = getPercent(rdata.memRealUsed, rdata.memTotal);
            var memText = Math.round(rdata.memRealUsed) + "/" + Math.round(rdata.memTotal) + " (MB)";
            percent = Math.round(percent);
            $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px' }).html("<span style='display:none'>" + percent + "</span>" + lan.index.memre_ok);
            setCookie("mem-before", memText);
            var memNull = Math.round(getCookie("memRealUsed") - rdata.memRealUsed);
            setTimeout(function () {
                if (memNull > 0) {
                    $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px', 'line-height': '22px', 'padding-top': '22px' }).html("<span style='display:none'>" + percent + "</span>" + lan.index.memre_ok_1 + "<br>" + memNull + "MB");
                } else {
                    $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px' }).html("<span style='display:none'>" + percent + "</span>" + lan.index.memre_ok_2);
                }
                $(".mem-release").removeClass("mem-action mem-releasing");
                $("#memory").text(memText);
                setCookie("memRealUsed", rdata.memRealUsed);
                setImg(); // Update the circle indicator based on new percentage
            }, 1000);
            setTimeout(function () {
                $(".mem-release").find('.mask').removeAttr("style").html("<span>" + percent + "</span>%");
                $(".mem-release").find(".mem-re-min").show();
                setImg(); // Ensure final position is set
            }, 2000)
        }, 'json');
    }, 2000);
}

function getPercent(num, total) {
    num = parseFloat(num);
    total = parseFloat(total);
    if (isNaN(num) || isNaN(total)) {
        return "-";
    }
    return total <= 0 ? "0%" : (Math.round(num / total * 10000) / 100.00);
}

function getDiskInfo() {
    $.get('/system/disk_info', function (rdata) {
        var dBody;
        for (var i = 0; i < rdata.length; i++) {
            var LoadColor = setcolor(parseInt(rdata[i].size[3].replace('%', '')), false, 75, 90, 95);

            var inodes = '';
            if (typeof (rdata[i]['inodes']) !== 'undefined') {
                inodes = '<div class="mask" style="color:' + LoadColor + '" data="Info Inode<br>Total: ' + rdata[i].inodes[0] + '<br>Terpakai: ' + rdata[i].inodes[1] + '<br>Tersedia: ' + rdata[i].inodes[2] + '<br>Penggunaan Inode: ' + rdata[i].inodes[3] + '"><span>' + rdata[i].size[3].replace('%', '') + '</span>%</div>';

                var ipre = parseInt(rdata[i].inodes[3].replace('%', ''));
                if (ipre > 95) {
                    $("#messageError").show();
                    $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>Partisi [' + rdata[i].path + '] penggunaan Inode sekarang lebih dari ' + ipre + '%. Kalau sampai 100%, kamu nggak bakal bisa bikin file lagi di partisi ini. Buruan bersihin ya! <a class="btlink" href="javascript:ClearSystem();">[Bersihin sampah]</a></p>');
                }
            }

            if (rdata[i].path == '/' || rdata[i].path == '/www') {
                if (rdata[i].size[2].indexOf('M') != -1) {
                    $("#messageError").show();
                    $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span> ' + lan.get('diskinfo_span_1', [rdata[i].path]) + ' <a class="btlink" href="javascript:ClearSystem();">[Bersihin sampah]</a></p>');
                }
            }

            dBody = '<li class="col-xs-6 col-sm-3 col-md-3 col-lg-2 mtb20 circle-box text-center diskbox">' +
                '<h3 class="c5 f15">' + rdata[i].path + '</h3>' +
                '<div class="circle" style="background:' + LoadColor + '">' +
                '<div class="pie_left">' +
                '<div class="left"></div>' +
                '</div>' +
                '<div class="pie_right">' +
                '<div class="right"></div>' +
                '</div>' + inodes + '</div>' +
                '<h4 class="c5 f15">' + rdata[i].size[1] + '/' + rdata[i].size[0] + '</h4>' +
                '</li>'
            $("#systemInfoList").append(dBody);
            setImg();
        }
    }, 'json');
}

function clearSystem() {
    var loadT = layer.msg('Lagi bersihin sampah sistem <img src="/static/img/ing.gif">', { icon: 16, time: 0, shade: [0.3, "#000"] });
    $.get('/system?action=ClearSystem', function (rdata) {
        layer.close(loadT);
        layer.msg('Bersih-bersih selesai, total ada [' + rdata[0] + '] file yang dibuang, dan [' + toSize(rdata[1]) + '] ruang disk dibebasin!', { icon: 1 });
    });
}

function setMemImg(info) {
    setCookie("memRealUsed", parseInt(info.memRealUsed));
    $("#memory").html(parseInt(info.memRealUsed) + '/' + parseInt(info.memTotal) + ' (MB)');
    setCookie("mem-before", $("#memory").text());
    if (!getCookie('memSize')) setCookie('memSize', parseInt(info.memTotal));
    var memPre = Math.floor(info.memRealUsed / (info.memTotal / 100));
    $("#left").html(memPre);
    setcolor(memPre, "#left", 75, 90, 95);
    $("#state").html(info.cpuRealUsed);
    setcolor(memPre, "#state", 30, 70, 90);
    setImg();
}

function getInfo() {
    $.get("/system/system_total", function (info) {
        setCookie("memRealUsed", parseInt(info.memRealUsed));
        $("#memory").html(parseInt(info.memRealUsed) + '/' + parseInt(info.memTotal) + ' (MB)');
        setCookie("mem-before", $("#memory").text());
        if (!getCookie('memSize')) setCookie('memSize', parseInt(info.memTotal));
        var memPre = Math.floor(info.memRealUsed / (info.memTotal / 100));
        $("#left").html(memPre);
        setcolor(memPre, "#left", 75, 90, 95);
        $("#info").html(info.system);
        $("#running").html(info.time);
        var _system = info.system;
        if (_system.indexOf("Windows") != -1) {
            $(".ico-system").addClass("ico-windows");
        } else if (_system.indexOf("CentOS") != -1) {
            $(".ico-system").addClass("ico-centos");
        } else if (_system.indexOf("Ubuntu") != -1) {
            $(".ico-system").addClass("ico-ubuntu");
        } else if (_system.indexOf("Debian") != -1) {
            $(".ico-system").addClass("ico-debian");
        } else if (_system.indexOf("Fedora") != -1) {
            $(".ico-system").addClass("ico-fedora");
        } else if (_system.indexOf("Mac") != -1 || _system.toLowerCase().indexOf("mac") != -1) {
            $(".ico-system").addClass("ico-mac");
        } else {
            $(".ico-system").addClass("ico-linux");
        }
        $("#core").html(info.cpuNum + ' Core');
        $("#state").html(info.cpuRealUsed);
        setcolor(memPre, "#state", 30, 70, 90);
        var memFree = info.memTotal - info.memRealUsed;

        if (memFree < 64) {
            $("#messageError").show();
            $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;">' + lan.index.mem_warning + '</span> </p>')
        }

        setImg();
    }, 'json');
}


function setcolor(pre, s, s1, s2, s3) {
    var LoadColor;
    if (pre <= s1) {
        LoadColor = '#20a53a';
    } else if (pre <= s2) {
        LoadColor = '#6ea520';
    } else if (pre <= s3) {
        LoadColor = '#ff9900';
    } else {
        LoadColor = '#dd2f00';
    }
    if (s == false) {
        return LoadColor;
    }
    var co = $(s).parent('.mask');
    co.css("color", LoadColor);
    co.parent('.circle').css("background", LoadColor);
}


function getNet() {
    var up, down;
    $.get("/system/network", function (net) {
        $("#InterfaceSpeed").html("Kecepatan Interface： 1.0Gbps");
        $("#upSpeed").html(net.up + ' KB');
        $("#downSpeed").html(net.down + ' KB');
        $("#downAll").html(toSize(net.downTotal));
        $("#downAll").attr('title', lan.index.package + ':' + net.downPackets)
        $("#upAll").html(toSize(net.upTotal));
        $("#upAll").attr('title', lan.index.package + ':' + net.upPackets)
        $("#core").html(net.cpu[1] + " " + lan.index.cpu_core);
        $("#state").html(net.cpu[0]);
        setcolor(net.cpu[0], "#state", 30, 70, 90);
        setCookie("upNet", net.up);
        setCookie("downNet", net.down);
        getLoad(net.load);

        // setMemImg(net.mem);
        setImg();

        showCpuTips(net);
    }, 'json');
}

function netImg() {
    var myChartNetwork = echarts.init(document.getElementById('netImg'));
    var xData = [];
    var yData = [];
    var zData = [];

    function getTime() {
        var now = new Date();
        var hour = now.getHours();
        var minute = now.getMinutes();
        var second = now.getSeconds();
        if (minute < 10) {
            minute = "0" + minute;
        }
        if (second < 10) {
            second = "0" + second;
        }
        var nowdate = hour + ":" + minute + ":" + second;
        return nowdate;
    }

    function ts(m) { return m < 10 ? '0' + m : m }

    function format(sjc) {
        var time = new Date(sjc);
        var h = time.getHours();
        var mm = time.getMinutes();
        var s = time.getSeconds();
        return ts(h) + ':' + ts(mm) + ':' + ts(s);
    }

    function addData(shift) {
        xData.push(getTime());
        yData.push(getCookie("upNet"));
        zData.push(getCookie("downNet"));
        if (shift) {
            xData.shift();
            yData.shift();
            zData.shift();
        }
    }
    for (var i = 8; i >= 0; i--) {
        var time = (new Date()).getTime();
        xData.push(format(time - (i * 3 * 1000)));
        yData.push(0);
        zData.push(0);
    }

    var option = {
        title: {
            text: lan.index.interface_net,
            left: 'center',
            textStyle: {
                color: '#888888',
                fontStyle: 'normal',
                fontFamily: lan.index.net_font,
                fontSize: 16,
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        legend: {
            data: [lan.index.net_up, lan.index.net_down],
            bottom: '2%'
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: xData,
            axisLine: {
                lineStyle: {
                    color: "#666"
                }
            }
        },
        yAxis: {
            name: lan.index.unit + 'KB/s',
            splitLine: {
                lineStyle: {
                    color: "#eee"
                }
            },
            axisLine: {
                lineStyle: {
                    color: "#666"
                }
            }
        },
        series: [{
            name: lan.index.net_up,
            type: 'line',
            data: yData,
            smooth: true,
            showSymbol: false,
            symbol: 'circle',
            symbolSize: 6,
            areaStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                        offset: 0,
                        color: 'rgba(255, 140, 0,0.5)'
                    }, {
                        offset: 1,
                        color: 'rgba(255, 140, 0,0.8)'
                    }], false)
                }
            },
            itemStyle: {
                normal: {
                    color: '#f7b851'
                }
            },
            lineStyle: {
                normal: {
                    width: 1
                }
            }
        }, {
            name: lan.index.net_down,
            type: 'line',
            data: zData,
            smooth: true,
            showSymbol: false,
            symbol: 'circle',
            symbolSize: 6,
            areaStyle: {
                normal: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                        offset: 0,
                        color: 'rgba(30, 144, 255,0.5)'
                    }, {
                        offset: 1,
                        color: 'rgba(30, 144, 255,0.8)'
                    }], false)
                }
            },
            itemStyle: {
                normal: {
                    color: '#52a9ff'
                }
            },
            lineStyle: {
                normal: {
                    width: 1
                }
            }
        }]
    };
    setInterval(function () {
        getNet();
        addData(true);
        myChartNetwork.setOption({
            xAxis: {
                data: xData
            },
            series: [{
                name: lan.index.net_up,
                data: yData
            }, {
                name: lan.index.net_down,
                data: zData
            }]
        });
    }, 3000);

    myChartNetwork.setOption(option);
    window.addEventListener("resize", function () {
        myChartNetwork.resize();
    });
}


function setImg() {
    $('.circle').each(function (index, el) {
        var num = $(this).find('span').text() * 3.6;
        if (num <= 180) {
            $(this).find('.left').css('transform', "rotate(0deg)");
            $(this).find('.right').css('transform', "rotate(" + num + "deg)");
        } else {
            $(this).find('.right').css('transform', "rotate(180deg)");
            $(this).find('.left').css('transform', "rotate(" + (num - 180) + "deg)");
        };
    });

    $('.diskbox .mask').unbind();
    $('.diskbox .mask').hover(function () {
        layer.closeAll('tips');
        var that = this;
        var conterError = $(this).attr("data");
        layer.tips(conterError, that, { time: 0, tips: [1, '#999'] });
    }, function () {
        layer.closeAll('tips');
    });
}

setTimeout(function () {
    $.get('/system/update_server?type=check', function (rdata) {
        if (rdata.status == false) return;
        if (rdata.data != undefined) {
            $("#toUpdate").html('<a class="btlink" href="javascript:updateMsg();">Perbarui</a>');
            $('#toUpdate a').html('Perbarui<i style="display: inline-block; color: red; font-size: 40px;position: absolute;top: -35px; font-style: normal; right: -8px;">.</i>');
            $('#toUpdate a').css("position", "relative");
            return;
        }
    }, 'json').error(function () {
    });
}, 3000);

function checkUpdate() {
    var loadT = layer.msg(lan.index.update_get, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/system/update_server?type=check', function (rdata) {
        layer.close(loadT);

        if (rdata.data == 'download') {
            updateStatus(); return;
        }

        if (rdata.status === false) {
            layer.confirm(rdata.msg, { title: lan.index.update_check, icon: 1, closeBtn: 1, btn: [lan.public.ok, lan.public.close] });
            return;
        }
        layer.msg(rdata.msg, { icon: 1 });
        if (rdata.data != undefined) updateMsg();
    }, 'json');
}

function updateMsg() {
    $.get('/system/update_server?type=info', function (rdata) {

        if (rdata.data == 'download') {
            updateStatus(); return;
        }

        var v = rdata.data.version;
        var v_info = '';
        if (v.split('.').length > 3) {
            v_info = "<span class='label label-warning'>Versi testing</span>";
        } else {
            v_info = "<span class='label label-success arrowed'>Versi resmi</span>";
        }

        layer.open({
            type: 1,
            title: v_info + '<span class="badge badge-inverse">Upgrade ke [' + rdata.data.version + ']</span>',
            area: '400px',
            shadeClose: false,
            closeBtn: 2,
            content: '<div class="setchmod bt-form pd20 pb70">'
                + '<p style="padding: 0 0 10px;line-height: 24px;">' + rdata.data.content + '</p>'
                + '<div class="bt-form-submit-btn">'
                + '<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">Batal</button>'
                + '<button type="button" class="btn btn-success btn-sm btn-title" onclick="updateVersion(\'' + rdata.data.version + '\')" >Update</button>'
                + '</div>'
                + '</div>'
        });
    }, 'json');
}


function updateVersion(version) {
    var loadT = layer.msg('Panel SLEMP lagi di-upgrade..', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/system/update_server?type=update&version=' + version, function (rdata) {

        layer.closeAll();
        if (rdata.status === false) {
            layer.msg(rdata.msg, { icon: 5, time: 5000 });
            return;
        }
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            $("#btversion").html(version);
            $("#toUpdate").html('');
        }
    }, 'json').error(function () {
        layer.msg('Gagal update, coba lagi ya!', { icon: 2 });
        setTimeout(function () {
            window.location.reload();
        }, 3000);
    });
}

function pluginIndexService(pname, pfunc, callback) {
    $.post('/plugins/run', { name: 'openresty', func: pfunc }, function (data) {
        if (!data.status) {
            layer.msg(data.msg, { icon: 0, time: 2000, shade: [0.3, '#000'] });
            return;
        }

        if (typeof (callback) == 'function') {
            callback(data);
        }
    }, 'json');
}

function reBoot() {
    layer.open({
        type: 1,
        title: 'Restart server atau panel',
        area: '330px',
        closeBtn: 1,
        shadeClose: false,
        content: '<div class="rebt-con"><div class="rebt-li"><a data-id="server" href="javascript:;">Restart server</a></div><div class="rebt-li"><a data-id="panel" href="javascript:;">Restart panel</a></div></div>'
    });


    $('.rebt-con a').click(function () {
        var type = $(this).attr('data-id');
        switch (type) {
            case 'panel':
                layer.confirm('Layanan Panel SLEMP bakal di-restart, lanjut?', { title: 'Restart layanan panel', closeBtn: 1, icon: 3 }, function () {
                    var loadT = layer.load();
                    $.post('/system/restart', '', function (rdata) {
                        layer.close(loadT);
                        layer.msg(rdata.msg);
                        setTimeout(function () { window.location.reload(); }, 3000);
                    }, 'json');
                });
                break;
            case 'server':
                var rebootbox = layer.open({
                    type: 1,
                    title: 'Restart server dengan aman',
                    area: ['500px', '280px'],
                    closeBtn: 1,
                    shadeClose: false,
                    content: "<div class='bt-form bt-window-restart'>\
                            <div class='pd15'>\
                            <p style='color:red; margin-bottom:10px; font-size:15px;'>Catatan: Kalau server kamu itu container (kayak Docker), mending batalin aja.</p>\
                            <div class='SafeRestart' style='line-height:26px'>\
                                <p>Reboot Aman bantu jagain file kamu dan bakal ngelakuin ini:</p>\
                                <p>1. Matikan layanan web</p>\
                                <p>2. Matikan layanan MySQL</p>\
                                <p>3. Mulai restart server</p>\
                                <p>4. Tunggu server nyala lagi</p>\
                            </div>\
                            </div>\
                            <div class='bt-form-submit-btn'>\
                                <button type='button' class='btn btn-danger btn-sm btn-reboot'>Batal</button>\
                                <button type='button' class='btn btn-success btn-sm WSafeRestart' >Restart</button>\
                            </div>\
                        </div>"
                });
                setTimeout(function () {
                    $(".btn-reboot").click(function () {
                        rebootbox.close();
                    })
                    $(".WSafeRestart").click(function () {
                        var body = '<div class="SafeRestartCode pd15" style="line-height:26px"></div>';
                        $(".bt-window-restart").html(body);
                        $(".SafeRestartCode").append("<p>Lagi matikan layanan web</p>");
                        pluginIndexService('openresty', 'stop', function (r1) {
                            $(".SafeRestartCode p").addClass('c9');
                            $(".SafeRestartCode").append("<p>Lagi matikan layanan MySQL...</p>");
                            pluginIndexService('mysql', 'stop', function (r2) {
                                $(".SafeRestartCode p").addClass('c9');
                                $(".SafeRestartCode").append("<p>Mulai restart server...</p>");
                                $.post('/system/restart_server', '', function (rdata) {
                                    $(".SafeRestartCode p").addClass('c9');
                                    $(".SafeRestartCode").append("<p>Tunggu server nyala lagi...</p>");
                                    var sEver = setInterval(function () {
                                        $.get("/system/system_total", function (info) {
                                            clearInterval(sEver);
                                            $(".SafeRestartCode p").addClass('c9');
                                            $(".SafeRestartCode").append("<p>Server berhasil di-restart!...</p>");
                                            setTimeout(function () {
                                                layer.closeAll();
                                            }, 3000);
                                        })
                                    }, 3000);
                                })
                            })
                        })
                    })
                }, 100);
                break;
        }
    });
}

function repPanel() {
    layer.confirm(lan.index.rep_panel_msg, { title: lan.index.rep_panel_title, closeBtn: 1, icon: 3 }, function (confirmIndex) {
        // Close confirm dialog
        layer.close(confirmIndex);
        
        // Open gorgeous dark-themed realtime terminal console
        layer.open({
            type: 1,
            title: 'Realtime Repair Console - SLEMP Panel',
            area: ['720px', '460px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div style="background-color: #121214; color: #e4e4e7; font-family: Consolas, Monaco, monospace; padding: 18px; height: 400px; overflow-y: auto; font-size: 13px; line-height: 1.6;" id="rep-terminal"></div>',
            success: function(layero, index) {
                var $terminal = $('#rep-terminal');
                $terminal.append('<p style="color: #3b82f6;">[System] Menghubungkan ke repositori utama SLEMP...</p>');
                
                // Stream output via HTML5 fetch reader API
                fetch('/system?action=RepPanel')
                    .then(response => {
                        const reader = response.body.getReader();
                        const decoder = new TextDecoder("utf-8");
                        
                        function readChunk() {
                            return reader.read().then(({ done, value }) => {
                                if (value) {
                                    const chunk = decoder.decode(value, { stream: !done });
                                    const escaped = chunk.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                                    $terminal.append(escaped.replace(/\n/g, '<br/>'));
                                    $terminal.scrollTop($terminal[0].scrollHeight);
                                }
                                if (done) {
                                    $terminal.append('<p style="color: #10b981; font-weight: bold; margin-top: 15px;">[Selesai] Perbaikan panel sukses! Halaman akan disegarkan dalam 3 detik...</p>');
                                    $terminal.scrollTop($terminal[0].scrollHeight);
                                    setTimeout(function() {
                                        window.location.reload();
                                    }, 3000);
                                    return;
                                }
                                return readChunk();
                            });
                        }
                        return readChunk();
                    })
                    .catch(error => {
                        // If we already received some log output, the panel likely restarted itself as part of the update!
                        if ($terminal.text().length > 70) {
                            $terminal.append('<p style="color: #10b981; font-weight: bold; margin-top: 15px;">[Selesai] Panel sedang memuat ulang (restarting) setelah perbaikan... Halaman akan disegarkan otomatis dalam 5 detik...</p>');
                            $terminal.scrollTop($terminal[0].scrollHeight);
                            setTimeout(function() {
                                window.location.reload();
                            }, 5000);
                        } else {
                            $terminal.append('<p style="color: #ef4444; margin-top: 10px;">[Error] Koneksi gagal: ' + error + '</p>');
                        }
                    });
            }
        });
    });
}

function getWarning() {
    $.get('/ajax?action=GetWarning', function (wlist) {
        var num = 0;
        for (var i = 0; i < wlist.data.length; i++) {
            if (wlist.data[i].ignore_count >= wlist.data[i].ignore_limit) continue;
            if (wlist.data[i].ignore_time != 0 && (wlist.time - wlist.data[i].ignore_time) < wlist.data[i].ignore_timeout) continue;
            var btns = '';
            for (var n = 0; n < wlist.data[i].btns.length; n++) {
                if (wlist.data[i].btns[n].type == 'javascript') {
                    btns += '<a href="javascript:WarningTo(\'' + wlist.data[i].btns[n].url + '\',' + wlist.data[i].btns[n].reload + ');" class="' + wlist.data[i].btns[n].class + '"> ' + wlist.data[i].btns[n].title + '</a>'
                } else {
                    btns += '<a href="' + wlist.data[i].btns[n].url + '" class="' + wlist.data[i].btns[n].class + '" target="' + wlist.data[i].btns[n].target + '"> ' + wlist.data[i].btns[n].title + '</a>'
                }
            }
            $("#messageError").append('<p><img src="' + wlist.icon[wlist.data[i].icon] + '" style="margin-right:14px;vertical-align:-3px">' + wlist.data[i].body + btns + '</p>');
            num++;
        }
        if (num > 0) $("#messageError").show();
    });
}

function warningTo(to_url, def) {
    var loadT = layer.msg(lan.public.the_get, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post(to_url, {}, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status && def) setTimeout(function () { location.reload(); }, 1000);
    }, 'json');
}

function setSafeHide() {
    setCookie('safeMsg', '1');
    $("#safeMsg").remove();
}

function showDanger(num, port) {
    var atxt = "Karena nggak pakai isolasi login, semua IP bisa nyoba masuk. Bahaya banget nih, buruan diurus ya!";
    if (port == "22") {
        atxt = "Karena port default SSH 22 belum diganti dan nggak pakai isolasi login, semua IP bisa nyoba masuk. Risiko tinggi, buruan benerin!";
    }
    layer.open({
        type: 1,
        area: ['720px', '410px'],
        title: 'Peringatan keamanan (kalau nggak mau dapet peringatan lagi, hapus aja plugin security login)',
        closeBtn: 1,
        shift: 5,
        content: '<div class="pd20">\
				<table class="f14 showDanger"><tbody>\
				<tr><td class="text-right" width="150">Jenis risiko: </td><td class="f16" style="color:red">brute force <a href="https://github.com/basoro/slemp/wiki/Interpretasi-dan-pertahanan-cracking-serangan-arak-pada-SSH" class="btlink f14" style="margin-left:10px" target="_blank">penjelasan</a></td></tr>\
				<tr><td class="text-right">Total serangan yang kedeteksi: </td><td class="f16" style="color:red">' + num + ' <a href="javascript:showDangerIP();" class="btlink f14" style="margin-left:10px">detail</a><span class="c9 f12" style="margin-left:10px">（Data diambil langsung dari log server）</span></td></tr>\
				<tr><td class="text-right">Tingkat risiko: </td><td class="f16" style="color:red">risiko tinggi</td></tr>\
				<tr><td class="text-right" style="vertical-align:top">Deskripsi risiko: </td><td style="line-height:20px">' + atxt + '</td></tr>\
				<tr><td class="text-right" style="vertical-align:top">Solusi yang ada: </td><td><p style="margin-bottom:8px">Solusi: Ganti port default SSH, pakai sertifikat digital buat login, dan hapus log login terakhir. </p></td></tr>\
				</tbody></table>\
				<div class="mtb20 text-center"><a href="https://github.com/basoro/slemp" target="_blank" class="btn btn-success">Pasang proteksi isolasi sekarang</a></div>\
				</div>'
    });
    $(".showDanger td").css("padding", "8px")
}

function pluginInit() {
    $.post('/plugins/init', function (data) {
        if (!data.status) {
            return false;
        }

        var rdata = data.data;
        var plugin_list = '';

        for (var i = 0; i < rdata.length; i++) {
            var ver = rdata[i]['versions'];
            var select_list = '';
            if (typeof (ver) == 'string') {
                select_list = '<option value="' + ver + '">' + rdata[i]['title'] + ' - ' + ver + '</option>';
            } else {
                for (var vi = 0; vi < ver.length; vi++) {

                    if (ver[vi] == rdata[i]['default_ver']) {
                        select_list += '<option value="' + ver[vi] + '" selected="selected">' + rdata[i]['title'] + ' - ' + ver[vi] + '</option>';
                    } else {
                        select_list += '<option value="' + ver[vi] + '">' + rdata[i]['title'] + ' - ' + ver[vi] + '</option>';
                    }
                }
            }

            var pn_checked = '<input id="data_' + rdata[i]['name'] + '" type="checkbox" checked>';
            if (rdata[i]['name'] == 'swap') {
                var pn_checked = '<input id="data_' + rdata[i]['name'] + '" type="checkbox" disabled="disabled" checked>';
            }

            plugin_list += '<li><span class="ico"><img src="/plugins/file?name=' + rdata[i]['name'] + '&f=ico.png"></span>\
            <span class="name">\
                <select id="select_'+ rdata[i]['name'] + '" class="sl-s-info">' + select_list + '</select>\
            </span>\
            <span class="pull-right">'+ pn_checked + '</span></li>';
        }

        layer.open({
            type: 1,
            title: 'Rekomendasi instalasi',
            area: ["337px", "403px"],
            closeBtn: 2,
            shadeClose: false,
            content: "\
        <div class='rec-install'>\
            <div class='important-title'>\
                <p><span class='glyphicon glyphicon-alert' style='color: #f39c12; margin-right: 10px;'></span>Ini aplikasi yang direkomendasiin <a href='javascript:jump()' style='color:#20a53a'>aplikasi</a>.</p>\
            </div>\
            <div class='rec-box'>\
                <h3 style='text-align: center'>Classic LNMP</h3>\
                <div class='rec-box-con'>\
                    <ul class='rec-list'>" + plugin_list + "</ul>\
                    <div class='onekey'>Install</div>\
                </div>\
            </div>\
        </div>",
            success: function (l, index) {
                $('.rec-box-con .onekey').click(function () {
                    var post_data = [];
                    for (var i = 0; i < rdata.length; i++) {
                        var key_ver = '#select_' + rdata[i]['name'];
                        var key_checked = '#data_' + rdata[i]['name'];

                        var val_checked = $(key_checked).prop("checked");
                        if (val_checked) {

                            var tmp = {};
                            var val_key = $(key_ver).val();

                            tmp['version'] = val_key;
                            tmp['name'] = rdata[i]['name'];
                            post_data.push(tmp);
                        }
                    }

                    $.post('/plugins/init_install', 'list=' + JSON.stringify(post_data), function (data) {
                        showMsg(data.msg, function () {
                            if (data.status) {
                                layer.closeAll();
                                messageBox();
                            }
                        }, { icon: data.status ? 1 : 2 }, 2000);
                    }, 'json');
                });
            },
            cancel: function () {
                layer.confirm('Whether to no longer show recommended installation kits?', { btn: ['Yes', 'Cancel'], title: "Do not show recommendations again?" }, function () {
                    $.post('/files/create_dir', 'path=' + SLEMP_ROOT_PATH + '/server/php', function (rdata) {
                        layer.closeAll();
                    }, 'json');
                });
            }
        });
    }, 'json');
}

function loadKeyDataCount() {
    var plist = ['mysql', 'gogs', 'gitea'];
    for (var i = 0; i < plist.length; i++) {
        pname = plist[i];
        function call(pname) {
            $.post('/plugins/run', { name: pname, func: 'get_total_statistics' }, function (data) {
                try {
                    var rdata = $.parseJSON(data['data']);
                } catch (e) {
                    return;
                }
                if (!rdata['status']) {
                    return;
                }
                var html = '<li class="sys-li-box col-xs-3 col-sm-3 col-md-3 col-lg-3">\
                        <p class="name f15 c9">'+ pname + '</p>\
                        <div class="val"><a class="btlink" onclick="softMain(\''+ pname + '\',\'' + pname + '\',\'' + rdata['data']['ver'] + '\')">' + rdata['data']['count'] + '</a></div>\
                    </li>';
                $('#index_overview').append(html);
            }, 'json');
        }
        call(pname);
    }
}

function manageDatabase() {
    var loadT = layer.msg('Lagi cek database...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/plugins/init_install', '', function (rdata) {
        layer.close(loadT);
        var dbPlugin = null;
        for (var i = 0; i < rdata.length; i++) {
            if ((rdata[i].name === 'mysql' || rdata[i].name === 'mariadb') && rdata[i].setup) {
                dbPlugin = rdata[i];
                break;
            }
        }
        if (dbPlugin) {
            if (typeof softMain === 'function') {
                softMain(dbPlugin.name, dbPlugin.title, dbPlugin.setup_version);
            } else {
                $.getScript('/static/app/soft.js?v=' + new Date().getTime(), function () {
                    softMain(dbPlugin.name, dbPlugin.title, dbPlugin.setup_version);
                });
            }
        } else {
            layer.msg('Plugin database belum terpasang.', { icon: 2 });
        }
    }, 'json');
}

function addDatabaseModal() {
    var loadT = layer.msg('Lagi cek database...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/plugins/init_install', '', function (rdata) {
        layer.close(loadT);
        var dbPlugin = null;
        for (var i = 0; i < rdata.length; i++) {
            if ((rdata[i].name === 'mysql' || rdata[i].name === 'mariadb') && rdata[i].setup) {
                dbPlugin = rdata[i];
                break;
            }
        }

        if (dbPlugin) {
            var loadS = layer.msg("Menyiapkan form...", { icon: 16, time: 0, shade: [0.3, '#000'] });
            $.get('/plugins/setting?name=' + dbPlugin.name, function (html) {
                layer.close(loadS);
                // Open the plugin management modal hidden or minimized to initialize JS
                var layerIdx = layer.open({
                    type: 1,
                    area: '640px',
                    title: dbPlugin.title + ' Manajemen',
                    closeBtn: 1,
                    shift: 0,
                    content: html,
                    success: function (layero, index) {
                        // Check for addDatabase function every 200ms
                        var checkJs = setInterval(function () {
                            if (typeof addDatabase === 'function') {
                                clearInterval(checkJs);
                                addDatabase(); // Open the actual "Add Database" modal
                            }
                        }, 200);

                        // Limit the check to 5 seconds to prevent infinite loop
                        setTimeout(function () { clearInterval(checkJs); }, 5000);
                    }
                });
            });
        } else {
            layer.msg('Plugin database belum terpasang.', { icon: 2 });
        }
    }, 'json');
}

$(function() {
    $(".mem-release").hover(function() {
        $(this).addClass("shine_green");
        if (!($(this).hasClass("mem-action"))) {
            $(this).find(".mem-re-min").hide();
            $(this).find(".mask").css({ "color": "#d2edd8" });
            $(this).find(".mem-re-con").css({ "display": "block" });
            $(this).find(".mem-re-con").animate({ "top": "0", opacity: 1 });
            $("#memory").text(lan.index.memre);
        }
    }, function() {
        $(this).removeClass("shine_green");
        $(this).find(".mask").css({ "color": "#20a53a" });
        $(this).find(".mem-re-con").css({ "top": "15px", opacity: 1, "display": "none" });
        $("#memory").text(getCookie("mem-before"));
        $(this).find(".mem-re-min").hide();
    }).click(function() {
        $(this).find(".mem-re-min").hide();
        if (!($(this).hasClass("mem-action"))) {
            reMemory();
            var btlen = $(".mem-release").find(".mask span").text();
            $(this).addClass("mem-action");
            $(this).find(".mask").css({ "color": "#20a53a" });
            $(this).find(".mem-re-con").animate({ "top": "-400px", opacity: 0 });
            $(this).find(".pie_right .right").css({ "transform": "rotate(3deg)" });
            for (var i = 0; i < btlen; i++) {
                setTimeout("rocket(" + btlen + "," + i + ")", i * 30);
            }
        }
    });
});

function getLoad(data) {
    $("#LoadList .mask").html("<span id='Load' style='font-size:14px'>Getting information..</span>");
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
        AverageText = 'Run smoothly';
    } else if (Occupy <= 70) {
        LoadColor = '#6ea520';
        AverageText = 'Operating normally';
    } else if (Occupy <= 90) {
        LoadColor = '#ff9900';
        AverageText = 'Sun slowly';
    } else {
        LoadColor = '#dd2f00';
        AverageText = 'Running jam';
    }
    index.find('.circle').css("background", LoadColor);
    index.find('.mask').css({ "color": LoadColor });
    $("#LoadList .mask").html("<span id='Load'></span>%");
    $('#Load').html(Occupy);
    $('#LoadState').html('<span>' + AverageText + '</span>');
    setImg();
}

$('#LoadList .circle').click(function() {
    getNet();
});

$('#LoadList .mask').hover(function() {
    var one, five, fifteen;
    var that = this;
    one = getCookie('one');
    five = getCookie('five');
    fifteen = getCookie('fifteen');
    var text = 'Average load in the last 1 minute: ' + one + '</br> Average load in the last 5 minutes: ' + five + '</br> Average load in the last 15 minutes: ' + fifteen + '';
    layer.tips(text, that, { time: 0, tips: [1, '#999'] });
}, function() {
    layer.closeAll('tips');
});


function showCpuTips(rdata){
    $('#cpuChart .mask').unbind();
    $('#cpuChart .mask').hover(function() {
        var cpuText = '';

        if (rdata.cpu[2].length == 1){
            var cpuUse = parseFloat(rdata.cpu[2][0] == 0 ? 0 : rdata.cpu[2][0]).toFixed(1);
            cpuText += 'CPU-1：' + cpuUse + '%'
        } else{
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
        layer.tips(rdata.cpu[3] + "</br>" + rdata.cpu[5] + " physical CPU, " + (rdata.cpu[4]) + " physical core, " + rdata.cpu[1] + " logical core</br>" + cpuText, this, { time: 0, tips: [1, '#999'] });
    }, function() {
        layer.closeAll('tips');
    });
}


function rocket(sum, m) {
    var n = sum - m;
    $(".mem-release").find(".mask span").text(n);
}

function reMemory() {
    setTimeout(function() {
        $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px' }).html('<span style="display:none">1</span>' + lan.index.memre_ok_0 + ' <img src="/static/img/ings.gif">');
        $.post('/system/rememory', '', function(rdata) {
            var percent = getPercent(rdata.memRealUsed, rdata.memTotal);
            var memText = Math.round(rdata.memRealUsed) + "/" + Math.round(rdata.memTotal) + " (MB)";
            percent = Math.round(percent);
            $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px' }).html("<span style='display:none'>" + percent + "</span>" + lan.index.memre_ok);
            setCookie("mem-before", memText);
            var memNull = Math.round(getCookie("memRealUsed") - rdata.memRealUsed);
            setTimeout(function() {
                if (memNull > 0) {
                    $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px', 'line-height': '22px', 'padding-top': '22px' }).html("<span style='display:none'>" + percent + "</span>" + lan.index.memre_ok_1 + "<br>" + memNull + "MB");
                } else {
                    $(".mem-release").find('.mask').css({ 'color': '#20a53a', 'font-size': '14px' }).html("<span style='display:none'>" + percent + "</span>" + lan.index.memre_ok_2);
                }
                $(".mem-release").removeClass("mem-action");
                $("#memory").text(memText);
                setCookie("memRealUsed", rdata.memRealUsed);
            }, 1000);
            setTimeout(function() {
                $(".mem-release").find('.mask').removeAttr("style").html("<span>" + percent + "</span>%");
                $(".mem-release").find(".mem-re-min").show();
            }, 2000)
        },'json');
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
    $.get('/system/disk_info', function(rdata) {
        var dBody;
        for (var i = 0; i < rdata.length; i++) {
            var LoadColor = setcolor(parseInt(rdata[i].size[3].replace('%', '')), false, 75, 90, 95);

            var inodes = '';
            if ( typeof(rdata[i]['inodes']) !=='undefined' ){
                inodes = '<div class="mask" style="color:' + LoadColor + '" data="Inode Information<br>Total：' + rdata[i].inodes[0] + '<br>Used：' + rdata[i].inodes[1] + '<br>Available：' + rdata[i].inodes[2] + '<br>Inode usage：' + rdata[i].inodes[3] + '"><span>' + rdata[i].size[3].replace('%', '') + '</span>%</div>';

                var ipre = parseInt(rdata[i].inodes[3].replace('%', ''));
                if (ipre > 95) {
                    $("#messageError").show();
                    $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>Partition [' + rdata[i].path + '] current Inode usage exceeds ' + ipre + '%. When the usage is 100%, files cannot be created in this partition. Please clean it up in time! <a class="btlink" href="javascript:ClearSystem();">[Clean up trash]</a></p>');
                }
            }

            if (rdata[i].path == '/' || rdata[i].path == '/www') {
                if (rdata[i].size[2].indexOf('M') != -1) {
                    $("#messageError").show();
                    $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span> ' + lan.get('diskinfo_span_1', [rdata[i].path]) + ' <a class="btlink" href="javascript:ClearSystem();">[Clean up trash]</a></p>');
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
                '</div>'+ inodes +'</div>' +
                '<h4 class="c5 f15">' + rdata[i].size[1] + '/' + rdata[i].size[0] + '</h4>' +
                '</li>'
            $("#systemInfoList").append(dBody);
            setImg();
        }
    },'json');
}

function clearSystem() {
    var loadT = layer.msg('Cleaning up system junk <img src="/static/img/ing.gif">', { icon: 16, time: 0, shade: [0.3, "#000"] });
    $.get('/system?action=ClearSystem', function(rdata) {
        layer.close(loadT);
        layer.msg('Cleanup is complete, a total of [' + rdata[0] + '] files will be cleaned up, and [' + toSize(rdata[1]) + '] disk space will be released!', { icon: 1 });
    });
}

function setMemImg(info){
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
    $.get("/system/system_total", function(info) {
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
        if(_system.indexOf("Windows") != -1){
            $(".ico-system").addClass("ico-windows");
        } else if(_system.indexOf("CentOS") != -1) {
            $(".ico-system").addClass("ico-centos");
        } else if(_system.indexOf("Ubuntu") != -1) {
            $(".ico-system").addClass("ico-ubuntu");
        } else if(_system.indexOf("Debian") != -1) {
            $(".ico-system").addClass("ico-debian");
        } else if(_system.indexOf("Fedora") != -1) {
            $(".ico-system").addClass("ico-fedora");
        } else if(_system.indexOf("Mac") != -1){
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
    },'json');
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
    $.get("/system/network", function(net) {
        $("#InterfaceSpeed").html(lan.index.interfacespeed + "： 1.0Gbps");
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
    },'json');
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
    setInterval(function() {
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
    window.addEventListener("resize", function() {
        myChartNetwork.resize();
    });
}


function setImg() {
    $('.circle').each(function(index, el) {
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
    $('.diskbox .mask').hover(function() {
        layer.closeAll('tips');
        var that = this;
        var conterError = $(this).attr("data");
        layer.tips(conterError, that, { time: 0, tips: [1, '#999'] });
    }, function() {
        layer.closeAll('tips');
    });
}

setTimeout(function() {
    $.get('/system/update_server?type=check', function(rdata) {
        if (rdata.status == false) return;
        if (rdata.data != undefined) {
            $("#toUpdate").html('<a class="btlink" href="javascript:updateMsg();">Renew</a>');
            $('#toUpdate a').html('Renew<i style="display: inline-block; color: red; font-size: 40px;position: absolute;top: -35px; font-style: normal; right: -8px;">.</i>');
            $('#toUpdate a').css("position","relative");
            return;
        }
    },'json').error(function() {
    });
}, 3000);

function checkUpdate() {
    var loadT = layer.msg(lan.index.update_get, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/system/update_server?type=check', function(rdata) {
        layer.close(loadT);

        if (rdata.data == 'download'){
            updateStatus();return;
        }

        if (rdata.status === false) {
            layer.confirm(rdata.msg, { title: lan.index.update_check, icon: 1, closeBtn: 1, btn: [lan.public.ok, lan.public.close] });
            return;
        }
        layer.msg(rdata.msg, { icon: 1 });
        if (rdata.data != undefined) updateMsg();
    },'json');
}

function updateMsg(){
    $.get('/system/update_server?type=info',function(rdata){

        if (rdata.data == 'download'){
            updateStatus();return;
        }

        var v = rdata.data.version;
        var v_info = '';
        if (v.split('.').length>3){
            v_info = "<span class='label label-warning'>Test version</span>";
        } else {
            v_info = "<span class='label label-success arrowed'>Official version</span>";
        }

        layer.open({
            type:1,
            title:v_info + '<span class="badge badge-inverse">Upgrade to ['+rdata.data.version+']</span>',
            area: '400px',
            shadeClose:false,
            closeBtn:2,
            content:'<div class="setchmod bt-form pd20 pb70">'
                    +'<p style="padding: 0 0 10px;line-height: 24px;">'+rdata.data.content+'</p>'
                    +'<div class="bt-form-submit-btn">'
                    +'<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">Cancel</button>'
                    +'<button type="button" class="btn btn-success btn-sm btn-title" onclick="updateVersion(\''+rdata.data.version+'\')" >Update</button>'
                    +'</div>'
                    +'</div>'
        });
    },'json');
}


function updateVersion(version) {
    var loadT = layer.msg('SLEMP Panel is being upgraded..', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/system/update_server?type=update&version='+version, function(rdata) {

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
    },'json').error(function() {
        layer.msg('Update failed, please try again!', { icon: 2 });
        setTimeout(function() {
            window.location.reload();
        }, 3000);
    });
}

function pluginIndexService(pname,pfunc, callback){
    $.post('/plugins/run', {name:'openresty', func:pfunc}, function(data) {
        if (!data.status){
            layer.msg(data.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }

        if(typeof(callback) == 'function'){
            callback(data);
        }
    },'json');
}

function reBoot() {
    layer.open({
        type: 1,
        title: 'Restart the server or panel',
        area: '330px',
        closeBtn: 1,
        shadeClose: false,
        content: '<div class="rebt-con"><div class="rebt-li"><a data-id="server" href="javascript:;">Restart server</a></div><div class="rebt-li"><a data-id="panel" href="javascript:;">Restart panel</a></div></div>'
    });


    $('.rebt-con a').click(function () {
        var type = $(this).attr('data-id');
        switch (type) {
            case 'panel':
                layer.confirm('SLEMP Panel service will be restarted soon, continue?', { title: 'Restart panel service', closeBtn: 1, icon: 3 }, function () {
                    var loadT = layer.load();
                    $.post('/system/restart','',function (rdata) {
                        layer.close(loadT);
                        layer.msg(rdata.msg);
                        setTimeout(function () { window.location.reload(); }, 3000);
                    },'json');
                });
                break;
            case 'server':
                var rebootbox = layer.open({
                    type: 1,
                    title: 'Restart the server safely',
                    area: ['500px', '280px'],
                    closeBtn: 1,
                    shadeClose: false,
                    content: "<div class='bt-form bt-window-restart'>\
                            <div class='pd15'>\
                            <p style='color:red; margin-bottom:10px; font-size:15px;'>Note, if your server is a container, please cancel.</p>\
                            <div class='SafeRestart' style='line-height:26px'>\
                                <p>Safe Reboot helps keep your files safe and will do the following:</p>\
                                <p>1. Stop the web service</p>\
                                <p>2. Stop the MySQL service</p>\
                                <p>3. Start restarting the server</p>\
                                <p>4. Wait for the server to start</p>\
                            </div>\
                            </div>\
                            <div class='bt-form-submit-btn'>\
                                <button type='button' class='btn btn-danger btn-sm btn-reboot'>Cancel</button>\
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
                        $(".SafeRestartCode").append("<p>Stopping web service</p>");
                        pluginIndexService('openresty', 'stop', function (r1) {
                            $(".SafeRestartCode p").addClass('c9');
                            $(".SafeRestartCode").append("<p>Stopping the MySQL service...</p>");
                            pluginIndexService('mysql','stop', function (r2) {
                                $(".SafeRestartCode p").addClass('c9');
                                $(".SafeRestartCode").append("<p>Start restarting the server...</p>");
                                $.post('/system/restart_server', '',function (rdata) {
                                    $(".SafeRestartCode p").addClass('c9');
                                    $(".SafeRestartCode").append("<p>Wait for the server to start...</p>");
                                    var sEver = setInterval(function () {
                                       $.get("/system/system_total", function(info) {
                                            clearInterval(sEver);
                                            $(".SafeRestartCode p").addClass('c9');
                                            $(".SafeRestartCode").append("<p>The server restarted successfully!...</p>");
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
    layer.confirm(lan.index.rep_panel_msg, { title: lan.index.rep_panel_title, closeBtn: 1, icon: 3 }, function() {
        var loadT = layer.msg(lan.index.rep_panel_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.get('/system?action=RepPanel', function(rdata) {
            layer.close(loadT);
            layer.msg(lan.index.rep_panel_ok, { icon: 1 });
        }).error(function() {
            layer.close(loadT);
            layer.msg(lan.index.rep_panel_ok, { icon: 1 });
        });
    });
}

function getWarning() {
    $.get('/ajax?action=GetWarning', function(wlist) {
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
    $.post(to_url, {}, function(rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status && def) setTimeout(function() { location.reload(); }, 1000);
    },'json');
}

function setSafeHide() {
    setCookie('safeMsg', '1');
    $("#safeMsg").remove();
}

function showDanger(num, port) {
    var atxt = "Because the security isolation login is not used, all IPs can try to connect, and there is a high risk, please deal with it immediately.";
    if (port == "22") {
        atxt = "Since the default port 22 of SSH has not been modified, and security isolation is not used to log in, all IPs can try to connect, and there is a high risk, please deal with it immediately.";
    }
    layer.open({
        type: 1,
        area: ['720px', '410px'],
        title: 'Security reminder (if you want to give up any security reminder notification, please delete the security login plugin)',
        closeBtn: 1,
        shift: 5,
        content: '<div class="pd20">\
				<table class="f14 showDanger"><tbody>\
				<tr><td class="text-right" width="150">Risk type：</td><td class="f16" style="color:red">brute force <a href="https://github.com/basoro/slemp/wiki/Interpretasi-dan-pertahanan-cracking-serangan-arak-pada-SSH" class="btlink f14" style="margin-left:10px" target="_blank">explain</a></td></tr>\
				<tr><td class="text-right">The cumulative total number of attacks encountered：</td><td class="f16" style="color:red">' + num + ' <a href="javascript:showDangerIP();" class="btlink f14" style="margin-left:10px">detailed</a><span class="c9 f12" style="margin-left:10px">（The data comes directly from this server log）</span></td></tr>\
				<tr><td class="text-right">Risk level：</td><td class="f16" style="color:red">higher risk</td></tr>\
				<tr><td class="text-right" style="vertical-align:top">Risk description：</td><td style="line-height:20px">' + atxt + '</td></tr>\
				<tr><td class="text-right" style="vertical-align:top">Solutions available：</td><td><p style="margin-bottom:8px">Solution: Modify the SSH default port, modify the SSH authentication method to digital certificate, and clear recent login logs. </p></td></tr>\
				</tbody></table>\
				<div class="mtb20 text-center"><a href="https://www.bt.cn/admin/index.html" target="_blank" class="btn btn-success">Deploy isolation protection now</a></div>\
				</div>'
    });
    $(".showDanger td").css("padding", "8px")
}

function pluginInit(){
    $.post('/plugins/init', function(data){
        if (!data.status){
            return false;
        }

        var rdata = data.data;
        var plugin_list = '';

        for (var i = 0; i < rdata.length; i++) {
            var ver = rdata[i]['versions'];
            var select_list = '';
            if (typeof(ver)=='string'){
                select_list = '<option value="' + ver +'">' + rdata[i]['title'] + ' - ' + ver + '</option>';
            } else {
                for (var vi = 0; vi < ver.length; vi++) {

                    if (ver[vi] == rdata[i]['default_ver']){
                        select_list += '<option value="'+ver[vi]+'" selected="selected">'+ rdata[i]['title'] + ' - '+ ver[vi] + '</option>';
                    } else {
                        select_list += '<option value="'+ver[vi]+'">'+ rdata[i]['title'] + ' - '+ ver[vi] + '</option>';
                    }
                }
            }

            var pn_checked = '<input id="data_'+rdata[i]['name']+'" type="checkbox" checked>';
            if (rdata[i]['name'] == 'swap'){
                var pn_checked = '<input id="data_'+rdata[i]['name']+'" type="checkbox" disabled="disabled" checked>';
            }

            plugin_list += '<li><span class="ico"><img src="/plugins/file?name='+rdata[i]['name']+'&f=ico.png"></span>\
            <span class="name">\
                <select id="select_'+rdata[i]['name']+'" class="sl-s-info">'+select_list+'</select>\
            </span>\
            <span class="pull-right">'+pn_checked+'</span></li>';
        }

        layer.open({
            type: 1,
            title: 'Recommended installation',
            area: ["337px", "403px"],
            closeBtn: 2,
            shadeClose: false,
            content:"\
        <div class='rec-install'>\
            <div class='important-title'>\
                <p><span class='glyphicon glyphicon-alert' style='color: #f39c12; margin-right: 10px;'></span>The following are recommended <a href='javascript:jump()' style='color:#20a53a'>application</a>.</p>\
            </div>\
            <div class='rec-box'>\
                <h3 style='text-align: center'>Classic LNMP</h3>\
                <div class='rec-box-con'>\
                    <ul class='rec-list'>" + plugin_list + "</ul>\
                    <div class='onekey'>Install</div>\
                </div>\
            </div>\
        </div>",
            success:function(l,index){
                $('.rec-box-con .onekey').click(function(){
                    var post_data = [];
                    for (var i = 0; i < rdata.length; i++) {
                        var key_ver = '#select_'+rdata[i]['name'];
                        var key_checked = '#data_'+rdata[i]['name'];

                        var val_checked = $(key_checked).prop("checked");
                        if (val_checked){

                            var tmp = {};
                            var val_key = $(key_ver).val();

                            tmp['version'] = val_key;
                            tmp['name'] = rdata[i]['name'];
                            post_data.push(tmp);
                        }
                    }

                    $.post('/plugins/init_install', 'list='+JSON.stringify(post_data), function(data){
                        showMsg(data.msg, function(){
                            if (data.status){
                                layer.closeAll();
                                messageBox();
                            }
                        },{ icon: data.status ? 1 : 2 },2000);
                    },'json');
                });
            },
            cancel:function(){
                layer.confirm('Whether to no longer show recommended installation kits?', {btn : ['Yes', 'Cancel'],title: "Do not show recommendations again?"}, function() {
                    $.post('/files/create_dir', 'path=/home/slemp/server/php', function(rdata) {
                        layer.closeAll();
                    },'json');
                });
            }
        });
    },'json');
}

function loadKeyDataCount(){
    var plist = ['mysql', 'gogs', 'gitea'];
    for (var i = 0; i < plist.length; i++) {
        pname = plist[i];
        function call(pname){
            $.post('/plugins/run', {name:pname, func:'get_total_statistics'}, function(data) {
                try {
                    var rdata = $.parseJSON(data['data']);
                } catch(e){
                    return;
                }
                if (!rdata['status']){
                    return;
                }
                var html = '<li class="sys-li-box col-xs-3 col-sm-3 col-md-3 col-lg-3">\
                        <p class="name f15 c9">'+pname+'</p>\
                        <div class="val"><a class="btlink" onclick="softMain(\''+pname+'\',\''+pname+'\',\''+rdata['data']['ver']+'\')">'+rdata['data']['count']+'</a></div>\
                    </li>';
                $('#index_overview').append(html);
            },'json');
        }
        call(pname);
    }
}

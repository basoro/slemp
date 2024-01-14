function web_shell2() {
    var termCols = 83;
    var termRows = 21;
    var sendTotal = 0;
    if(!socket)socket = io.connect();
    var term = new Terminal({ cols: termCols, rows: termRows, screenKeys: true, useStyle: true});

    term.open();
    term.setOption('cursorBlink', true);
    term.setOption('fontSize', 14);
    gterm = term

    socket.on('server_response', function (data) {
        term.write(data.data);
        if (data.data == '\r\nlogout\r\n' ||
            data.data == 'logout\r\n' ||
            data.data == '\r\nlogout\r\n' ||
            data.data == 'logout\r\n') {
            setTimeout(function () {
                layer.closeAll();
                term.destroy();
                clearInterval(interval);
            }, 500);
        }
    });

    if (socket) {
        socket.emit('connect_event', '');
        interval = setInterval(function () {
            socket.emit('connect_event', '');
        }, 1000);
    }

    term.on('data', function (data) {
        socket.emit('webssh', data);
    });


    var term_box = layer.open({
        type: 1,
        title: "Local terminal",
        area: ['685px','435px'],
        closeBtn: 2,
        shadeClose: false,
        content: '<div class="term-box"><div id="term"></div></div>\
					<div class="shell-text-input">\
                    <textarea type="text" class="bt-input-text-shell" placeholder="Please paste the command here.." value="" name="ssh_copy" />\
					<div class="shell-btn-group">\
                    <button class="shellbutton btn btn-success btn-sm pull-right shell_btn_1">Send (Ctrl+Enter)</button>\
					<button class="shellbutton btn btn-default btn-sm pull-right shell_btn_close">Close</button>\
					</div>\
                </div>',
        cancel: function () {
            term.destroy();
            clearInterval(interval);
        }
    });
	$(".shell_btn_close").click(function(){
		layer.close(term_box);
		term.destroy();
        clearInterval(interval);
	})

    setTimeout(function () {
        $('.terminal').detach().appendTo('#term');
        $("#term").show();
        socket.emit('webssh', "\n");
        term.focus();

        // right mouse button event
        var can = $("#term");
        can.contextmenu(function (e) {
            var winWidth = can.width();
            var winHeight = can.height();
            var mouseX = e.pageX;
            var mouseY = e.pageY;
            var menuWidth = $(".contextmenu").width();
            var menuHeight = $(".contextmenu").height();
            var minEdgeMargin = 10;
            if (mouseX + menuWidth + minEdgeMargin >= winWidth &&
                mouseY + menuHeight + minEdgeMargin >= winHeight) {
                menuLeft = mouseX - menuWidth - minEdgeMargin + "px";
                menuTop = mouseY - menuHeight - minEdgeMargin + "px";
            }
            else if (mouseX + menuWidth + minEdgeMargin >= winWidth) {
                menuLeft = mouseX - menuWidth - minEdgeMargin + "px";
                menuTop = mouseY + minEdgeMargin + "px";
            }
            else if (mouseY + menuHeight + minEdgeMargin >= winHeight) {
                menuLeft = mouseX + minEdgeMargin + "px";
                menuTop = mouseY - menuHeight - minEdgeMargin + "px";
            }
            else {
                menuLeft = mouseX + minEdgeMargin + "px";
                menuTop = mouseY + minEdgeMargin + "px";
            };

            var selectText = term.getSelection()
            var style_str = '';
            var paste_str = '';
            if (!selectText) {
                if (!getCookie('shell_copy_body')) {
                    paste_str = 'style="color: #bbb;" disable';
                }
                style_str = 'style="color: #bbb;" disable';
            } else {
                setCookie('ssh_selection', selectText);
            }


            var menudiv = '<ul class="contextmenu">\
                        <li><a class="shell_copy_btn menu_ssh" data-clipboard-text="'+ selectText + '" ' + style_str + '>Copy to clipboard</a></li>\
                        <li><a  onclick="shell_paste_text()" '+ paste_str+'>Paste selection</a></li>\
                    </ul>';
            $("body").append(menudiv);
            $(".contextmenu").css({
                "left": menuLeft,
                "top": menuTop
            });
            return false;
        });
        can.click(function () {
            remove_ssh_menu();
        });

        clipboard = new ClipboardJS('.shell_copy_btn');
        clipboard.on('success', function (e) {
            layer.msg('Copy successfully!');
            setCookie('shell_copy_body', e.text)
            remove_ssh_menu();
            term.focus();
        });

        clipboard.on('error', function (e) {
            layer.msg('Copy failed, browser is not compatible!');
            setCookie('shell_copy_body', e.text)
            remove_ssh_menu();
            term.focus();
        });

        $(".shellbutton").click(function () {
            var tobj = $("textarea[name='ssh_copy']");
            var ptext = tobj.val();
            tobj.val('');
            if ($(this).text().indexOf('Alt') != -1) {
                ptext +="\n";
            }
            socket.emit('webssh', ptext);
            term.focus();
        })
        $("textarea[name='ssh_copy']").keydown(function (e) {

            if (e.ctrlKey && e.keyCode == 13) {
                $(".shell_btn_1").click();
            } else if (e.altKey && e.keyCode == 13) {
                $(".shell_btn_1").click();
            }
        });

    }, 100);
}

function shell_paste_text(){
    socket.emit('webssh', getCookie('ssh_selection'));
    remove_ssh_menu();
    gterm.focus();
}

function remove_ssh_menu() {
    $(".contextmenu").remove();
}

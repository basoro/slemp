var ollama = {
    plugin_name: 'ollama',
    openwebui_install_timer: null,
    openwebui_install_layer: null,
    init: function () {},

    request: function (method, args, callback) {
        var data = {};
        data['name'] = 'ollama';
        data['func'] = method;
        data['version'] = $('.plugin_version').attr('version');

        if (typeof (args) == 'string') {
            data['args'] = JSON.stringify(toArrayObject(args));
        } else {
            data['args'] = JSON.stringify(args || {});
        }

        $.post('/plugins/run', data, function (res) {
            if (!res.status) {
                if (typeof (callback) == 'function') {
                    callback({ status: false, msg: res.msg, data: {} });
                }
                return;
            }

            var ret_data = $.parseJSON(res.data);
            if (typeof (callback) == 'function') {
                callback(ret_data);
            }
        }, 'json');
    },

    send: function (info) {
        var tips = info['tips'];
        var method = info['method'];
        var args = info['data'];
        var callback = info['success'];

        var loadT = layer.msg(tips, { icon: 16, time: 0, shade: 0.3 });

        var data = {};
        data['name'] = 'ollama';
        data['func'] = method;
        data['version'] = $('.plugin_version').attr('version');

        if (typeof (args) == 'string') {
            data['args'] = JSON.stringify(toArrayObject(args));
        } else {
            data['args'] = JSON.stringify(args);
        }

        $.post('/plugins/run', data, function (res) {
            layer.close(loadT);
            if (!res.status) {
                layer.msg(res.msg, { icon: 2, time: 10000 });
                return;
            }

            var ret_data = $.parseJSON(res.data);

            if (typeof (callback) == 'function') {
                callback(ret_data);
            }
        }, 'json');
    },

    postCallback: function (info) {
        var tips = info['tips'];
        var method = info['method'];
        var args = info['data'];
        var callback = info['success'];

        var loadT = layer.msg(tips, { icon: 16, time: 0, shade: 0.3 });

        var data = {};
        data['name'] = 'ollama';
        data['func'] = method;
        data['version'] = $('.plugin_version').attr('version');

        if (typeof (args) == 'string') {
            data['args'] = JSON.stringify(toArrayObject(args));
        } else {
            data['args'] = JSON.stringify(args);
        }

        $.post('/plugins/callback', data, function (res) {
            layer.close(loadT);
            if (!res.status) {
                layer.msg(res.msg, { icon: 2, time: 10000 });
                return;
            }

            var ret_data = $.parseJSON(res.data);
            if (!ret_data.status) {
                layer.msg(ret_data.msg, { icon: 2, time: 2000 });
                return;
            }

            if (typeof (callback) == 'function') {
                callback(res);
            }
        }, 'json');
    },

    openwebui: function () {
        var _this = this;

        this.send({
            'tips': 'Mendapatkan status OpenWebUI...',
            'method': 'openwebui_status',
            'data': {},
            'success': function (rdata) {
                _this.openwebuiShow(rdata);
            }
        });
    },

    openwebuiShow: function (rdata) {
        var status = rdata.data.status;
        var port = rdata.data.port || 8080;
        var install_cmds = rdata.data.install_cmds || [];
        var start_cmds = rdata.data.start_cmds || [];
        var status_text = '';
        var btn_install = '';
        var btn_start = '';
        var btn_stop = '';
        var btn_restart = '';
        var btn_uninstall = '';
        var port_info = '';
        var install_html = '';
        var start_html = '';

        for (var i = 0; i < install_cmds.length; i++) {
            install_html += '<code>' + install_cmds[i] + '</code><br>';
        }

        for (var j = 0; j < start_cmds.length; j++) {
            start_html += '<code>' + start_cmds[j] + '</code><br>';
        }

        if (status == 'python_not_supported') {
            status_text = '<span style="color:#ff9900">Python panel belum 3.11, gunakan virtualenv OpenWebUI</span>';
            btn_install = '<button class="btn btn-success btn-sm" onclick="ollama.openwebuiInstall()">Instal OpenWebUI</button>';
        } else if (status == 'not_installed') {
            status_text = '<span style="color:#ff9900">Belum diinstal</span>';
            btn_install = '<button class="btn btn-success btn-sm" onclick="ollama.openwebuiInstall()">Instal OpenWebUI</button>';
        } else if (status == 'stopped') {
            status_text = '<span style="color:#ff9900">Belum dijalankan</span>';
            btn_start = '<button class="btn btn-primary btn-sm" onclick="ollama.openwebuiStart()">Mulai</button>';
            btn_uninstall = '<button class="btn btn-danger btn-sm" onclick="ollama.openwebuiUninstall()">Hapus</button>';
        } else if (status == 'running') {
            status_text = '<span style="color:green">Berjalan</span>';
            port_info = '<p>Port: <a href="http://localhost:' + port + '" target="_blank">http://localhost:' + port + '</a></p>';
            btn_stop = '<button class="btn btn-warning btn-sm" onclick="ollama.openwebuiStop()">Hentikan</button>';
            btn_restart = '<button class="btn btn-primary btn-sm" onclick="ollama.openwebuiRestart()">Restart</button>';
            btn_uninstall = '<button class="btn btn-danger btn-sm" onclick="ollama.openwebuiUninstall()">Hapus</button>';
        }

        var con = '<div class="plugin-webui">';
        con += '<div class="line">';
        con += '<div class="info-r">';
        con += '<h4>OpenWebUI - Antarmuka Web untuk Ollama</h4>';
        con += '</div>';
        con += '</div>';
        con += '<div class="line">';
        con += '<div class="info-r">';
        con += '<p>Status: ' + status_text + '</p>';
        con += port_info;
        con += '</div>';
        con += '</div>';
        con += '<div class="line">';
        con += '<div class="info-r">';
        con += '<p style="margin-bottom:10px">OpenWebUI menyediakan antarmuka web yang intuitif untuk berinteraksi dengan model Ollama.</p>';
        con += '<ul style="margin-bottom:10px">';
        con += '<li>Antarmuka pengguna yang modern dan mudah digunakan</li>';
        con += '<li>Koneksi otomatis ke Ollama yang berjalan di host</li>';
        con += '<li>Tanpa autentikasi (untuk pengembangan lokal)</li>';
        con += '</ul>';
        con += '</div>';
        con += '</div>';
        con += '<div class="line">';
        con += '<div class="info-r">';
        con += '<p style="margin-bottom:10px"><b>Port:</b></p>';
        con += '<div class="input-group" style="width:200px">';
        con += '<input type="number" id="openwebui_port" class="form-control" value="' + port + '" min="1" max="65535">';
        con += '<span class="input-group-btn"><button class="btn btn-default" onclick="ollama.openwebuiSetPort()">Simpan</button></span>';
        con += '</div>';
        con += '<p style="margin-top:5px;color:#999;font-size:12px">Ubah port dan klik Simpan. Perlu restart setelah mengubah port.</p>';
        con += '</div>';
        con += '</div>';
        con += '<div class="line">';
        con += '<div class="info-r">';
        con += '<p style="margin-bottom:10px"><b>Perintah Instalasi OpenWebUI:</b></p>';
        con += install_html;
        con += '<p style="margin:10px 0 10px"><b>Perintah Menjalankan OpenWebUI:</b></p>';
        con += start_html;
        con += '<p style="margin-top:5px;color:#999;font-size:12px">Gunakan perintah di atas jika ingin memasang atau menjalankan OpenWebUI secara manual dari terminal.</p>';
        con += '</div>';
        con += '</div>';
        con += '<div class="line">';
        con += '<div class="info-r">';
        con += '<p style="margin-bottom:10px"><b>Perintah Ollama:</b></p>';
        con += '<code>ollama pull &lt;model&gt;</code> - Mengunduh model<br>';
        con += '<code>ollama run &lt;model&gt;</code> - Menjalankan model<br>';
        con += '<code>ollama list</code> - Daftar model<br>';
        con += '<code>ollama ps</code> - Model yang berjalan';
        con += '</div>';
        con += '</div>';
        con += '<div class="line">';
        con += '<div class="info-r" style="margin-top:15px">';
        con += btn_install + ' ' + btn_start + ' ' + btn_stop + ' ' + btn_restart + ' ' + btn_uninstall;
        con += '</div>';
        con += '</div>';
        con += '</div>';

        $('.soft-man-con').html(con);
    },

    openwebuiInstall: function () {
        var _this = this;
        this.send({
            'tips': 'Menginstal OpenWebUI...',
            'method': 'openwebui_install',
            'data': {},
            'success': function (rdata) {
                if (rdata.data && rdata.data.installing) {
                    _this.openwebuiInstallProgress();
                    return;
                }
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2, time: 3000 });
                if (rdata.status) {
                    setTimeout(function () {
                        _this.openwebui();
                    }, 2000);
                }
            }
        });
    },

    openwebuiInstallProgress: function () {
        var _this = this;
        if (this.openwebui_install_timer) {
            clearInterval(this.openwebui_install_timer);
            this.openwebui_install_timer = null;
        }

        var con = '';
        con += '<div class="bt-form pd15" style="padding-bottom:20px">';
        con += '<p id="openwebui_install_msg" style="margin-bottom:10px">Menyiapkan instalasi OpenWebUI...</p>';
        con += '<div style="height:12px;background:#f1f1f1;border-radius:10px;overflow:hidden">';
        con += '<div id="openwebui_install_bar" style="width:0%;height:12px;background:#20a53a;transition:width .3s"></div>';
        con += '</div>';
        con += '<p id="openwebui_install_percent" style="margin-top:8px;color:#666">0%</p>';
        con += '<pre id="openwebui_install_log" style="margin-top:10px;height:220px;overflow:auto;background:#111;color:#ddd;padding:10px;border-radius:4px;white-space:pre-wrap"></pre>';
        con += '</div>';

        this.openwebui_install_layer = layer.open({
            type: 1,
            title: 'Instalasi OpenWebUI',
            area: ['680px', '420px'],
            shadeClose: false,
            closeBtn: 1,
            content: con,
            cancel: function () {
                if (_this.openwebui_install_timer) {
                    clearInterval(_this.openwebui_install_timer);
                    _this.openwebui_install_timer = null;
                }
            }
        });

        var poll = function () {
            _this.request('openwebui_install_progress', {}, function (rdata) {
                var percent = 0;
                var msg = 'Menunggu status instalasi...';
                var log_text = '';
                var status = 'idle';

                if (rdata.data) {
                    percent = rdata.data.percent || 0;
                    msg = rdata.data.msg || msg;
                    log_text = rdata.data.log || '';
                    status = rdata.data.status || status;
                } else {
                    msg = rdata.msg || 'Gagal membaca status instalasi.';
                    status = 'failed';
                }

                $('#openwebui_install_bar').css('width', percent + '%');
                $('#openwebui_install_percent').text(percent + '%');
                $('#openwebui_install_msg').text(msg);
                $('#openwebui_install_log').text(log_text);
                var log_box = document.getElementById('openwebui_install_log');
                if (log_box) log_box.scrollTop = log_box.scrollHeight;

                if (status == 'success' || status == 'failed') {
                    if (_this.openwebui_install_timer) {
                        clearInterval(_this.openwebui_install_timer);
                        _this.openwebui_install_timer = null;
                    }
                    layer.msg(msg, { icon: status == 'success' ? 1 : 2, time: 4000 });
                    setTimeout(function () {
                        _this.openwebui();
                    }, 1500);
                }
            });
        };

        poll();
        this.openwebui_install_timer = setInterval(poll, 1500);
    },

    openwebuiStart: function () {
        var _this = this;
        this.send({
            'tips': 'Memulai OpenWebUI...',
            'method': 'openwebui_start',
            'data': {},
            'success': function (rdata) {
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2, time: 3000 });
                if (rdata.status) {
                    setTimeout(function () {
                        _this.openwebui();
                    }, 2000);
                }
            }
        });
    },

    openwebuiStop: function () {
        var _this = this;
        this.send({
            'tips': 'Menghentikan OpenWebUI...',
            'method': 'openwebui_stop',
            'data': {},
            'success': function (rdata) {
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2, time: 3000 });
                if (rdata.status) {
                    setTimeout(function () {
                        _this.openwebui();
                    }, 2000);
                }
            }
        });
    },

    openwebuiRestart: function () {
        var _this = this;
        this.send({
            'tips': 'Merestart OpenWebUI...',
            'method': 'openwebui_restart',
            'data': {},
            'success': function (rdata) {
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2, time: 3000 });
                if (rdata.status) {
                    setTimeout(function () {
                        _this.openwebui();
                    }, 2000);
                }
            }
        });
    },

    openwebuiUninstall: function () {
        var _this = this;
        layer.confirm('Yakin ingin menghapus OpenWebUI?', {
            btn: ['Ya', 'Batal']
        }, function () {
            _this.send({
                'tips': 'Menghapus OpenWebUI...',
                'method': 'openwebui_uninstall',
                'data': {},
                'success': function (rdata) {
                    layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2, time: 3000 });
                    if (rdata.status) {
                        setTimeout(function () {
                            _this.openwebui();
                        }, 2000);
                    }
                }
            });
        });
    },

    openwebuiSetPort: function () {
        var _this = this;
        var new_port = $('#openwebui_port').val();

        if (!new_port || new_port < 1 || new_port > 65535) {
            layer.msg('Port harus antara 1 dan 65535', { icon: 2, time: 2000 });
            return;
        }

        var data = 'port=' + encodeURIComponent(new_port);

        // Use postForm like phpmyadmin
        var loadT = layer.msg('Mengubah port...', { icon: 16, time: 0, shade: 0.3 });

        var post_data = {
            'name': 'ollama',
            'func': 'openwebui_set_port',
            'args': data
        };

        $.post('/plugins/run', post_data, function (res) {
            layer.close(loadT);
            if (!res.status) {
                layer.msg(res.msg, { icon: 2, time: 10000 });
                return;
            }

            var ret_data = $.parseJSON(res.data);
            layer.msg(ret_data.msg, { icon: ret_data.status ? 1 : 2, time: 3000 });
            if (ret_data.status) {
                setTimeout(function () {
                    _this.openwebui();
                }, 2000);
            }
        }, 'json');
    },

    readme: function () {
        var readme = '<ul class="help-info-text c7">';
        readme += '<li>Perintah Umum:</li>';
        readme += '</ul>';
        readme += '<div class="divtable mtb15">';
        readme += '<table class="table table-hover">';
        readme += '<thead><tr><th>Perintah</th><th>Deskripsi</th><th>Contoh</th></tr></thead>';
        readme += '<tbody>';
        readme += '<tr><td><code>ollama pull &lt;nama model&gt;</code></td><td>Mengunduh model yang ditentukan ke lokal saja, tidak langsung menjalankan</td><td><code>ollama pull deepseek-r1:7b</code></td></tr>';
        readme += '<tr><td><code>ollama run &lt;nama model&gt;</code></td><td>Mengunduh (jika belum ada secara lokal) dan menjalankan model, masuk ke antarmuka interaktif</td><td><code>ollama run llama3.2</code></td></tr>';
        readme += '<tr><td><code>ollama list</code></td><td>Menampilkan semua model yang telah diunduh ke lokal</td><td><code>ollama list</code></td></tr>';
        readme += '<tr><td><code>ollama ps</code></td><td>Melihat model yang sedang berjalan</td><td><code>ollama ps</code></td></tr>';
        readme += '<tr><td><code>ollama stop &lt;nama model&gt;</code></td><td>Menghentikan model yang sedang berjalan</td><td><code>ollama stop llama3.2</code></td></tr>';
        readme += '<tr><td><code>ollama rm &lt;nama model&gt;</code></td><td>Menghapus model tertentu dari lokal, membebaskan ruang disk</td><td><code>ollama rm llama3.2</code></td></tr>';
        readme += '<tr><td><code>ollama serve</code></td><td>Memulai layanan latar belakang Ollama (juga akan dimulai secara otomatis saat pertama kali menjalankan model)</td><td><code>ollama serve</code></td></tr>';
        readme += '</tbody></table></div>';
        $('.soft-man-con').html(readme);
    }
}


function owPost(method, args, callback){
    var loadT = layer.msg('Sedang mengambil...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'op_waf', func:method, args:JSON.stringify(args)}, function(data) {
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

function owPostN(method, args, callback){
    $.post('/plugins/run', {name:'op_waf', func:method, args:JSON.stringify(args)}, function(data) {
        if (!data.status){
            layer.msg(data.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }

        if(typeof(callback) == 'function'){
            callback(data);
        }
    },'json'); 
}


function getRuleByName(rule_name, callback){
    owPost('get_rule', {rule_name:rule_name}, function(data){
        callback(data);
    });
}


function setRequestCode(ruleName, statusCode){
    layer.open({
        type: 1,
        title: "Atur kode respons【" + ruleName + "】",
        area: '300px',
        shift: 5,
        closeBtn: 1,
        shadeClose: true,
        content: '<div class="bt-form pd20 pb70">\
                    <div class="line">\
                        <span class="tname">Kode respons</span>\
                        <div class="info-r">\
                            <select id="statusCode" class="bt-input-text mr5" style="width:150px;">\
                                <option value="200" '+ (statusCode == 200 ? 'selected' : '') + '>Normal(200)</option>\
                                <option value="404" '+ (statusCode == 404 ? 'selected' : '') + '>File tidak ada(404)</option>\
                                <option value="403" '+ (statusCode == 403 ? 'selected' : '') + '>Akses ditolak(403)</option>\
                                <option value="444" '+ (statusCode == 444 ? 'selected' : '') + '>Tutup koneksi(444)</option>\
                                <option value="500" '+ (statusCode == 500 ? 'selected' : '') + '>Kesalahan aplikasi(500)</option>\
                                <option value="502" '+ (statusCode == 502 ? 'selected' : '') + '>Koneksi habis waktu(502)</option>\
                                <option value="503" '+ (statusCode == 503 ? 'selected' : '') + '>Server tidak tersedia(503)</option>\
                            </select>\
                        </div>\
                    </div>\
                    <div class="bt-form-submit-btn">\
                        <button type="button" class="btn btn-success btn-sm btn-title" onclick="setState(\''+ ruleName + '\')">OK</button>\
                    </div>\
                </div>'
    });
}

function setState(ruleName){
    var statusCode = $('#statusCode').val();
    owPost('set_obj_status', {obj:ruleName,statusCode:statusCode},function(data){
        var rdata = $.parseJSON(data.data);
        if (rdata.status){
            layer.msg(rdata.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            wafGloabl();
        } else {
            layer.msg('Pengaturan gagal!',{icon:0,time:2000,shade: [0.3, '#000']});
        }
    });
}

function setObjOpen(ruleName){
    owPost('set_obj_open', {obj:ruleName},function(data){
        var rdata = $.parseJSON(data.data);
        if (rdata.status){

            showMsg(rdata.msg, function(){
                wafGloabl();
            },{icon:1,time:2000,shade: [0.3, '#000']},2000);
        } else {
            layer.msg('Pengaturan gagal!',{icon:0,time:2000,shade: [0.3, '#000']});
        }
    });
}


//SimpanCCAturan
function saveCcRule(siteName,is_open_global, type) {
    var increase = "0";
    if(type == 2){
        // set_aicc_open('start');
        increase = "0";
    } else {
        // set_aicc_open('stop');
        increase = type;
    }
    increase = "0";
    var pdata = {
        siteName:siteName,
        cycle: $("input[name='cc_cycle']").val(),
        limit: $("input[name='cc_limit']").val(),
        endtime: $("input[name='cc_endtime']").val(),
        is_open_global:is_open_global,
        increase:increase
    }
    console.log(pdata);
    var act = 'set_cc_conf';
    if (siteName != 'undefined') act = 'set_site_cc_conf';

    owPost(act, pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        setTimeout(function(){
            if (siteName != 'undefined') {
                siteWafConfig(siteName, 1);
            } else {
                wafGloabl();
            }
        },1000);
    });
}


function setCcRule(cycle, limit, endtime, siteName, increase){
    var incstr = '<li style="color:red;">Pengaturan di sini hanya berlaku untuk situs saat ini。</li>';
    if (siteName == 'undefined') {
        incstr = '<li style="color:red;">Nilai yang diatur di sini adalah nilai awal，Situs baru akan mewarisi，Tidak berlaku untuk situs yang ada。</li>';
    }
    // <div class="line">\
    //     <span class="tname">Mode ditingkatkan</span>\
    //     <div class="info-r">\
    //         <select class="bt-input-text mr5" style="width:80px" name="enhance_mode">\
    //             <option value="0" '+ (enhance_mode == 0?'selected':'') +'>Tutup</option>\
    //             <option value="1" '+ (enhance_mode == 1?'selected':'') +'>Aktifkan</option>\
    //         </select>\
    //     </div>\
    // </div>\
    // <div class="line" style="display:'+ (siteName == 'undefined'?'block':'none') +'">\
    //     <span class="tname">Pertahanan Layer 4</span>\
    //     <div class="info-r">\
    //         <select class="bt-input-text mr5" style="width:80px" name="cc_four_defense">\
    //             <option value="0">Tutup</option>\
    //             <option value="1">Aktifkan</option>\
    //         </select>\
    //     </div>\
    // </div>\
    //<li><font style="color:red;">Mode ditingkatkan:CCVersi Pertahanan Ditingkatkan，Mungkin memengaruhi pengalaman pengguna jika diaktifkan，Disarankan saat pengguna terkenaCCAktifkan saat serangan。</font></li>\

    create_l = layer.open({
        type: 1,
        title: "AturCCAturan",
        area: '540px',
        closeBtn: 1,
        shadeClose: false,
        content: '<form class="bt-form pd20 pb70">\
                <div class="line">\
                    <span class="tname">Siklus</span>\
                    <div class="info-r"><input class="bt-input-text" name="cc_cycle" type="number" value="'+ cycle + '" /> Detik</div>\
                </div>\
                <div class="line">\
                    <span class="tname">Frekuensi</span>\
                    <div class="info-r"><input class="bt-input-text" name="cc_limit" type="number" value="'+ limit + '" /> Kali</div>\
                </div>\
                <div class="line">\
                    <span class="tname">Waktu blokir</span>\
                    <div class="info-r"><input class="bt-input-text" name="cc_endtime" type="number" value="'+ endtime + '" /> Detik</div>\
                </div>\
                <ul class="help-info-text c7 ptb10">'+ incstr + '\
                    <li><font style="color:red;">'+ cycle + '</font> permintaan kumulatif dalam detik untuk hal yang samaURLMelebihi  <font style="color:red;">' + limit + '</font> Kali,PicuPertahanan CC,Blokir iniIP <font style="color:red;">' + endtime + '</font> Detik</li>\
                    <li>Jangan mengatur terlalu ketatCCAturan,agar tidak memengaruhi pengalaman pengguna normal</li>\
                    <li><font style="color:red;display:'+ (siteName == 'undefined'?'display: inline-block;':'none') +';">Terapkan secara global:Pengaturan global saat iniCCAturan，dan menimpa semua situs saat iniCCAturan</font></li>\
                </ul>\
                <div class="bt-form-submit-btn">\
                    <button type="button" class="btn btn-danger btn-sm btn_cc_all" style="margin-right:10px;display:'+ (siteName == 'undefined'?'display: inline-block;':'none') +';">Terapkan secara global</button>\
                    <button type="button" class="btn btn-success btn-sm btn_cc_present">Terapkan</button>\
                </div>\
            </form>',
            success:function(layero,index){
                $('.btn_cc_all').click(function(){
                    saveCcRule(siteName,1,$('[name="enhance_mode"]').val());
                });
                $('.btn_cc_present').click(function(){
                    saveCcRule(siteName,0,$('[name="enhance_mode"]').val());
                });
            }
    });
}


//AturretryAturan
function setRetry(retry_cycle, retry, retry_time, siteName) {
    create_layer = layer.open({
        type: 1,
        title: "Atur aturan toleransi kejahatan",
        area: '500px',
        closeBtn: 1,
        shadeClose: false,
        content: '<form class="bt-form pd20 pb70">\
                <div class="line">\
                    <span class="tname">Siklus</span>\
                    <div class="info-r"><input class="bt-input-text" name="retry_cycle" type="number" value="'+ retry_cycle + '" /> Detik</div>\
                </div>\
                <div class="line">\
                    <span class="tname">Frekuensi</span>\
                    <div class="info-r"><input class="bt-input-text" name="retry" type="number" value="'+ retry + '" /> Kali</div>\
                </div>\
                <div class="line">\
                    <span class="tname">Waktu blokir</span>\
                    <div class="info-r"><input class="bt-input-text" name="retry_time" type="number" value="'+ retry_time + '" /> Detik</div>\
                </div>\
                <ul class="help-info-text c7 ptb10">\
                    <li><font style="color:red;">'+ retry_cycle + '</font> permintaan jahat dalam detik melebihi  <font style="color:red;">' + retry + '</font> Kali,Blokir <font style="color:red;">' + retry_time + '</font> Detik</li>\
                    <li><font style="color:red;">Terapkan secara global:Pengaturan global aturan toleransi jahat saat ini，dan menimpa aturan toleransi jahat untuk semua situs</font></li>\
                </ul>\
                <div class="bt-form-submit-btn">\
                    <button type="button" class="btn btn-danger btn-sm btn_retry_all" style="margin-right:10px;display:'+ (siteName == undefined?'inline-block;':'none') +';">Terapkan secara global</button>\
                    <button type="button" class="btn btn-success btn-sm btn_retry_present">Terapkan</button>\
                </div>\
            </form>',
        success:function(){
            $('.btn_retry_all').click(function(){
                saveRetry(siteName,1);
            });
            $('.btn_retry_present').click(function(){
                saveRetry(siteName,0);
            });
        }
    });
}



//Atursafe_verifyAturan
function setSafeVerify(auto, cpu, time, mode,siteName) {
    var svlayer = layer.open({
        type: 1,
        title: "Atur verifikasi keamanan paksa",
        area: '500px',
        closeBtn: 1,
        shadeClose: false,
        content: '<form class="bt-form pd20 pb70">\
                <div class="line">\
                    <span class="tname">CPU</span>\
                    <div class="info-r"><input class="bt-input-text" name="cpu" type="number" max-number="100" value="'+ cpu + '" /> %</div>\
                </div>\
                <div class="line">\
                    <span class="tname">Waktu lewat</span>\
                    <div class="info-r">\
                        <input class="bt-input-text" name="time" type="number" value="'+ time + '" /> Detik\
                    </div>\
                </div>\
                <div class="line">\
                    <span class="tname">Mode verifikasi</span>\
                    <div class="info-r">\
                        <select class="bt-input-text mr5" style="width:200px" name="mode">\
                        <option value="url" '+(mode=='url'?"selected=selected":"")+'>URLVerifikasi lompatan</option>\
                        <option value="local" '+(mode=='local'?"selected=selected":"")+'>Verifikasi lokal</option>\
                        </select>\
                    </div>\
                </div>\
                <div class="line">\
                    <span class="tname">Aktifkan otomatis</span>\
                    <div class="info-r">\
                        <select class="bt-input-text mr5" style="width:80px" name="auto">\
                        <option value="0" '+(auto==false?"selected=selected":"")+'>Tutup</option>\
                        <option value="1" '+(auto==true?"selected=selected":"")+'>Aktifkan</option>\
                        </select>\
                    </div>\
                </div>\
                <ul class="help-info-text c7 ptb10">\
                    <li><font style="color:red;">Pengaturan global verifikasi keamanan paksa</font></li>\
                    <li>Setelah aktif otomatis:cpuMelebihi['+cpu+'%]Setelah，Verifikasi paksa。</li>\
                </ul>\
                <div class="bt-form-submit-btn">\
                    <button type="button" class="btn btn-success btn-sm btn_sv_present">Terapkan</button>\
                </div>\
            </form>',
        success:function(index){
            $('.btn_sv_present').click(function(){
                var pdata = {
                    siteName: siteName,
                    cpu: $("input[name='cpu']").val(),
                    auto: $("select[name='auto']").val(),
                    mode: $("select[name='mode']").val(),
                    time: $("input[name='time']").val(),
                }
                var act = 'set_safe_verify';
                owPost(act, pdata, function(data){
                    var rdata = $.parseJSON(data.data);
                    showMsg(rdata.msg, function() {
                       layer.close(svlayer);
                       wafGloabl();
                    },{ icon: rdata.status ? 1 : 2 },1000);
                });
            });   

            
        },
    });
}


//SimpanretryAturan
function saveRetry(siteName,type) {
    var pdata = {
        siteName: siteName,
        retry: $("input[name='retry']").val(),
        retry_time: $("input[name='retry_time']").val(),
        retry_cycle: $("input[name='retry_cycle']").val(),
        is_open_global:type
    }

    var act = 'set_retry';
    if (siteName != undefined) act = 'set_site_retry';
    owPost(act, pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        layer.close(create_layer);
        wafGloablRefresh(1000);
    });
}

function addRule(ruleName) {
    var pdata = {
        'ruleValue': $("input[name='ruleValue']").val(),
        'ps': $("input[name='rulePs']").val(),
        'ruleName': ruleName
    }

    owPost('add_rule', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
                setObjConf(ruleName, 1);
            },1000);
        }
    });
}

function modifyRule(index, ruleName) {
    var ruleValue = $('.rule_body_' + index).text();
    $('.rule_body_' + index).html('<textarea class="bt-input-text" name="rule_body_' + index + '" style="margin: 0px; height: 70px; width: 99%;line-height:20px">' + ruleValue + '</textarea>');
    var rulePs = $('.rule_ps_' + index).text();
    $('.rule_ps_' + index).html('<input class="bt-input-text" type="text" name="rule_ps_' + index + '" value="' + rulePs + '" />');
    $('.rule_modify_' + index).html('<a class="btlink" onclick="modifyRuleSave(' + index + ',\'' + ruleName + '\')">Simpan</a> | <a class="btlink modr_cancel_' + index + '">Batal</a>');
    $(".modr_cancel_" + index).click(function () {
        $('.rule_body_' + index).html(ruleValue);
        $('.rule_ps_' + index).html(rulePs);
        $('.rule_modify_' + index).html('<a class="btlink" onclick="modifyRule(' + index + ',\'' + ruleName + '\')">Edit</a>');
    })
}

function modifyRuleSave(index, ruleName) {
    var pdata = {
        index: index,
        ruleName: ruleName,
        ruleBody: $("textarea[name='rule_body_" + index + "']").val(),
        rulePs: $("input[name='rule_ps_" + index + "']").val()
    }

    owPost('modify_rule', pdata, function(data){
        var rdata = $.parseJSON(data.data);

        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
                setObjConf(ruleName, 1);
            },1000);
        }
    });
}

function removeRule(ruleName, index) {
    var pdata = {
        'index': index,
        'ruleName': ruleName
    }
    safeMessage('Hapus aturan', 'Apakah Anda yakin ingin menghapus aturan filter ini?？', function () {
        owPost('remove_rule', pdata, function(data){
            var rdata = $.parseJSON(data.data);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            if (rdata.status) {
                setTimeout(function(){
                    setObjConf(ruleName, 1);
                },1000);
            }
        });
    });
}

function setRuleState(ruleName, index) {
    var pdata = {
        'index': index,
        'ruleName': ruleName
    }
    
    owPost('set_rule_state', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
                setObjConf(ruleName, 1);
            },1000);
        }
    });
}

//Atur aturan
function setObjConf(ruleName, type) {
    if (type == undefined) {
        create_l = layer.open({
            type: 1,
            title: "Edit aturan【" + ruleName + "】",
            area: ['700px', '530px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="pd15">\
                <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                <input class="bt-input-text" name="ruleValue" type="text" value="" style="width:470px;margin-right:12px;" placeholder="Konten aturan,Silakan gunakan regex">\
                <input class="bt-input-text mr5" name="rulePs" type="text" style="width:120px;" placeholder="Deskripsi">\
                <button class="btn btn-success btn-sm va0 pull-right" onclick="addRule(\''+ ruleName + '\');">Tambah</button>\</div>\
                <div class="divtable">\
                <div id="jc-file-table" class="table_head_fix" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
                <table class="table table-hover" style="border:none">\
                    <thead>\
                        <tr>\
                            <th width="360">Aturan</th>\
                            <th>Penjelasan</th>\
                            <th>Operasi</th>\
                            <th style="text-align: right;">Status</th>\
                        </tr>\
                    </thead>\
                    <tbody id="set_obj_conf_con" class="gztr"></tbody>\
                </table>\
                </div>\
            </div>\
            <ul class="help-info-text c7 ptb10">\
                <li style="color:red;">Catatan:Jika Anda tidak mengerti regex,Jangan mengubah konten aturan sembarangan</li>\
                <li>Anda dapat menambah atau mengubah konten aturan,tapi silakan gunakan regex</li>\
                <li>Aturan bawaan boleh diubah,tapi tidak bisa dihapus langsung,Anda dapat mengatur status aturan untuk menentukan apakah firewall menggunakan aturan ini</li>\
            </ul></div>'
        });
        tableFixed("jc-file-table");
    }

    getRuleByName(ruleName, function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        var tbody = ''
        for (var i = 0; i < rdata.length; i++) {
            var removeRule = ''
            if (rdata[i][3] != 0) removeRule = ' | <a class="btlink" onclick="removeRule(\'' + ruleName + '\',' + i + ')">Hapus</a>';
            tbody += '<tr>\
                    <td class="rule_body_'+ i + '">' + rdata[i][1] + '</td>\
                    <td class="rule_ps_'+ i + '">' + rdata[i][2] + '</td>\
                    <td class="rule_modify_'+ i + '"><a class="btlink" onclick="modifyRule(' + i + ',\'' + ruleName + '\')">Edit</a>' + removeRule + '</td>\
                    <td class="text-right">\
                        <div class="pull-right">\
                        <input class="btswitch btswitch-ios" id="closeua_'+ i + '" type="checkbox" ' + (rdata[i][0] ? 'checked' : '') + '>\
                        <label class="btswitch-btn" style="width:2.0em;height:1.2em;margin-bottom: 0" for="closeua_'+ i + '" onclick="setRuleState(\'' + ruleName + '\',' + i + ')"></label>\
                        </div>\
                    </td>\
                </tr>'
        }
        $("#set_obj_conf_con").html(tbody);
    });
}


//Pemindai umum
function scanRule() {

    getRuleByName('scan_black', function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);

        create_l = layer.open({
            type: 1,
            title: "Aturan filter pemindai umum",
            area: '650px',
            closeBtn: 1,
            shadeClose: false,
            content: '<form class="bt-form pd20 pb70">\
                    <div class="line">\
                        <span class="tname">Header</span>\
                        <div class="info-r"><textarea style="margin: 0px;width:475px;height: 75px;line-height:20px" class="bt-input-text" name="scan_header" >'+ rdata.header + '</textarea></div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">Cookie</span>\
                        <div class="info-r"><textarea style="margin: 0px;width:475px;height: 75px;line-height:20px" class="bt-input-text" name="scan_cookie" >'+ rdata.cookie + '</textarea></div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">Args</span>\
                        <div class="info-r"><textarea style="margin: 0px;width:475px;height: 75px;line-height:20px" class="bt-input-text" name="scan_args" >'+ rdata.args + '</textarea></div>\
                    </div>\
                    <ul class="help-info-text c7 ptb10">\
                        <li>Akan memfilter secara bersamaankeydanvalue,Silakan atur dengan hati-hati</li>\
                        <li>Silakan gunakan regex,Cadangkan ekspresi asli sebelum mengirim</li>\
                    </ul>\
                    <div class="bt-form-submit-btn">\
                        <button type="button" class="btn btn-success btn-sm btn-title" onclick="saveScanRule()">OK</button>\
                    </div>\
                </form>'
        });
    });
}

//Simpan aturan pemindai
function saveScanRule() {
    pdata = {
        header: $("textarea[name='scan_header']").val(),
        cookie: $("textarea[name='scan_cookie']").val(),
        args: $("textarea[name='scan_args']").val()
    }
    owPost('save_scan_rule', pdata,function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        layer.close(create_l);
        wafGloablRefresh(1000);
    });
}

//TambahIPSegmen keIPDaftar Putih
function addIpWhite() {
    var pdata = {
        start_ip: $("input[name='start_ip']").val(),
        end_ip: $("input[name='end_ip']").val()
    }

    if (pdata['start_ip'].split('.').length < 4 || pdata['end_ip'].split('.').length < 4) {
        layer.msg('AwalIPatau berakhirIPFormat tidak benar!');
        return;
    }

    owPost('add_ip_white', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
               ipWhite(1); 
            },1000);
        }
    });
}

//DariIPHapus daftar putihIPSegmen
function removeIpWhite(index) {
    owPost('remove_ip_white', { index: index }, function(data){
        var rdata = $.parseJSON(data.data);
        if (rdata.status) {
            setTimeout(function(){
                ipWhite(1);
            },1000);   
        }
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}


function funDownload(content, filename) {
    // Buat tautan unduhan tersembunyi
    var eleLink = document.createElement('a');
    eleLink.download = filename;
    eleLink.style.display = 'none';
    // Konten karakter berubah menjadiblobAlamat
    var blob = new Blob([content]);
    eleLink.href = URL.createObjectURL(blob);
    // Picu klik
    document.body.appendChild(eleLink);
    eleLink.click();
    // lalu hapus
    document.body.removeChild(eleLink);
}

function outputLayer(rdata, name, type) {
    window.Load_layer = layer.open({
        type: 1,
        title: type ? "Ekspor data" : "Impor data",
        area: ['400px', '370px'],
        shadeClose: false,
        content: '<div class="soft-man-con" style="padding:10px;">' +
            '<div class="line">' +
            '<div class="ml0" style="position:relative;" id="focus_tips">' +
            '<textarea class="bt-input-text mr20 config" name="config" style="width: 300px; height: 250px; line-height: 22px; display: none;" id="lead_data">' + (rdata != '' ? JSON.stringify(rdata) : '') + '</textarea>' +
            '<div class="placeholder c9" style="top: 15px; left: 15px; display:' + (rdata == "" ? "block;" : "none;") + '">Format impor sebagai berikut：' +
            (name == 'ip_white' || name == 'ip_black' ? "[[[127, 0, 0, 1],[127, 0, 0, 255]],[[192, 0, 0, 1],[192, 0, 0, 255]]]" : "[\"^/test\",\"^/web\"]") +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="line "><div class="ml0">' +
            (type ? '<button name="btn_save_to" class="btn btn-success btn-sm mr5 btn_save_to" >Ekspor konfigurasi</button>' : '<button name="btn_save" class="btn btn-success btn-sm mr5 btn_save">Simpan</button>') +
            '</div></div>' +
            '</div>',
    });
    var lead_error = CodeMirror.fromTextArea(document.getElementById("lead_data"), {
        mode: 'html',
        matchBrackets: true,
        matchtags: true,
        autoMatchParens: true
    });
    setTimeout(function () {
        $('.btn_save').on('click', function () {
            importData(name, lead_error.getValue(), function(){
                layer.close(window.Load_layer);
                ipWhiteLoadList();
            });
        })
        $('.btn_save_to').on('click', function () {
            funDownload(lead_error.getValue(), name + '.json');
        });
        $('#focus_tips').on('click', function () {
            $('.placeholder').hide();
        });
    }, 100);
}


//Ekspor data
function outputData(name, callback) {
    var loadT = layer.msg('Sedang mengekspor data..', { icon: 16, time: 0 });

    owPost('output_data', { sname: name } , function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        if (callback) callback(rdata,res);
        outputLayer(rdata, name, true);
    });
}

//Impor data
function importData(name, pdata, callback) {
    owPost('import_data', { sname: name, pdata: pdata } , function(data){
        var rdata = $.parseJSON(data.data);   
        if (callback) callback();
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function fileInput(name) {
    outputLayer('', name, false);
}


function ipWhiteLoadList(){
    getRuleByName('ip_white', function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        var tbody = ''
        for (var i = 0; i < rdata.length; i++) {
            tbody += '<tr>\
                    <td>'+ rdata[i][0].join('.') + '</td>\
                    <td>'+ rdata[i][1].join('.') + '</td>\
                    <td class="text-right"><a class="btlink" onclick="removeIpWhite('+ i + ')">Hapus</a></td>\
                </tr>'
        }
        $("#ip_white_con").html(tbody);
    });
}
//IPDaftar Putih
function ipWhite(type) {
    if (type == undefined) {
        create_l = layer.open({
            type: 1,
            title: "ManajemenIPDaftar Putih",
            area: ['500px', '500px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="pd15 ipv4_list">\
                        <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                            <input class="bt-input-text" name="start_ip" type="text" value="" style="width:180px;margin-right:15px;margin-left:5px" placeholder="AwalIPAlamat">\
                            <input class="bt-input-text mr5" name="end_ip" type="text" style="width:180px;margin-left:5px;margin-right:20px" placeholder="SelesaiIPAlamat">\
                            <button class="btn btn-success btn-sm va0 pull-right" onclick="addIpWhite();">Tambah</button>\</div>\
                        <div class="divtable">\
                        <div id="ipWhite" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
                            <table class="table table-hover" style="border:none">\
                                <thead>\
                                    <tr>\
                                        <th>AwalIP</th>\
                                        <th>SelesaiIP</th>\
                                        <th style="text-align: right;">Operasi</th>\
                                    </tr>\
                                </thead>\
                                <tbody id="ip_white_con" class="gztr"></tbody>\
                            </table>\
                        </div>\
                    </div>\
                    <div style="width:100%" class="mt5">\
                        <button class="btn btn-success btn-sm va0 mr5 mt10" onclick="fileInput(\'ip_white\')" >Impor</button>\
                        <button class="btn btn-success btn-sm va0 mt10" onclick="outputData(\'ip_white\')">Ekspor</button>\
                    </div>\
                    <ul class="help-info-text c7 ptb10">\
                        <li>Semua aturan terhadap daftar putihIPSegmen tidak valid,TermasukIPDaftar hitam danURLDaftar Hitam,IPDaftar putih memiliki prioritas tertinggi</li>\
                    </ul>\
                </div>\
                <div class="pd15 ipv6_list">\
                </div>',
            success:function(index,layero){
                // $('.tab_list .tab_block').click(function(){
                //     $(this).addClass('active').siblings().removeClass('active');
                //     console.log($(this).index());
                //     if($(this).index() === 0){
                //         $('.ipv4_list').show().next().hide();
                //     }else{
                //         $('.ipv4_list').hide().next().show();
                //     }
                // });
                // <div class="tab_list"><div class="tab_block active">IPv4Daftar Putih</div><div class="tab_block">IPv6Daftar Putih</div></div>\
            }
        });
        tableFixed("ipWhite");
    }
    ipWhiteLoadList();
}

//IPDaftar Putih
function urlWhite(type) {

    var ruleName = "url_white";

    if (type == undefined) {
        create_l = layer.open({
            type: 1,
            title: "ManajemenURLDaftar Putih",
            area: ['700px', '530px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="pd15">\
                <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                <input class="bt-input-text" name="ruleValue" type="text" value="" style="width:470px;margin-right:12px;" placeholder="Konten aturan,Silakan gunakan regex">\
                <input class="bt-input-text mr5" name="rulePs" type="text" style="width:120px;" placeholder="Deskripsi">\
                <button class="btn btn-success btn-sm va0 pull-right" onclick="addRule(\''+ ruleName + '\');">Tambah</button>\</div>\
                <div class="divtable">\
                <div id="jc-file-table" class="table_head_fix" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
                <table class="table table-hover" style="border:none">\
                    <thead>\
                        <tr>\
                            <th width="360">Aturan</th>\
                            <th>Penjelasan</th>\
                            <th>Operasi</th>\
                            <th style="text-align: right;">Status</th>\
                        </tr>\
                    </thead>\
                    <tbody id="set_obj_conf_con" class="gztr"></tbody>\
                </table>\
                </div>\
            </div>\
            <ul class="help-info-text c7 ptb10">\
                <li style="color:red;">Catatan:Jika Anda tidak mengerti regex,Jangan mengubah konten aturan sembarangan</li>\
                <li>Anda dapat menambah atau mengubah konten aturan,tapi silakan gunakan regex</li>\
                <li>Aturan bawaan boleh diubah,tapi tidak bisa dihapus langsung,Anda dapat mengatur status aturan untuk menentukan apakah firewall menggunakan aturan ini</li>\
            </ul></div>'
        });
        tableFixed("jc-file-table");
    }

    getRuleByName(ruleName, function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        console.log(rdata);
        var tbody = ''
        for (var i = 0; i < rdata.length; i++) {
            var removeRule = ''
            if (rdata[i][3] != 0) removeRule = ' | <a class="btlink" onclick="removeRule(\'' + ruleName + '\',' + i + ')">Hapus</a>';
            tbody += '<tr>\
                    <td class="rule_body_'+ i + '">' + rdata[i][1] + '</td>\
                    <td class="rule_ps_'+ i + '">' + rdata[i][2] + '</td>\
                    <td class="rule_modify_'+ i + '"><a class="btlink" onclick="modifyRule(' + i + ',\'' + ruleName + '\')">Edit</a>' + removeRule + '</td>\
                    <td class="text-right">\
                        <div class="pull-right">\
                        <input class="btswitch btswitch-ios" id="closeua_'+ i + '" type="checkbox" ' + (rdata[i][0] ? 'checked' : '') + '>\
                        <label class="btswitch-btn" style="width:2.0em;height:1.2em;margin-bottom: 0" for="closeua_'+ i + '" onclick="setRuleState(\'' + ruleName + '\',' + i + ')"></label>\
                        </div>\
                    </td>\
                </tr>'
        }
        $("#set_obj_conf_con").html(tbody);
    });
}


// AmbilIPV4Daftar Hitam
function getIpv4Address(callback){
    getRuleByName('ip_black', function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        callback(rdata);
    });
}

// AmbilIPV6Daftar Hitam
function getIpv6Address(callback){
    getRuleByName('ipv6_black', function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        callback(rdata);
    });
}


// Tambahipv6Permintaan
function addIpv6Req(ip,callback){
    var ip = ip.replace(/:/g, '_');
    owPost('set_ipv6_black', {addr:ip}, function(data){
        var rdata = $.parseJSON(data.data);
        if(callback) callback(rdata);
    });
}

// Tambahipv6Permintaan
function removeIpv6Black(ip,callback){
    var ip = ip.replace(/:/g, '_');
    owPost('del_ipv6_black', {addr:ip}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg,{icon:rdata.status?1:2});
        $('.tab_list .tab_block:eq(1)').click();

        if(callback) callback(rdata);
    });
}

//TambahIPSegmen keIPDaftar Hitam
function addIpBlack() {
    var pdata = {
        start_ip: $("input[name='start_ip']").val(),
        end_ip: $("input[name='end_ip']").val()
    }

    if (pdata['start_ip'].split('.').length < 4 || pdata['end_ip'].split('.').length < 4) {
        layer.msg('AwalIPatau berakhirIPFormat tidak benar!');
        return;
    }

    owPost('add_ip_black', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        if (rdata.status) {
            ipBlack(1);
        }
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

function addIpBlackArgs(ip) {
    var pdata = {
        start_ip: ip,
        end_ip: ip,
    }

    if (pdata['start_ip'].split('.').length < 4 || pdata['end_ip'].split('.').length < 4) {
        layer.msg('AwalIPatau berakhirIPFormat tidak benar!');
        return;
    }

    owPost('add_ip_black', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}


//DariIPHapus daftar hitamIPSegmen
function removeIpBlack(index) {
    owPost('remove_ip_black', { index: index }, function (data) {
        var rdata = $.parseJSON(data.data);
        if (rdata.status) {
            ipBlack(1);
        }
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

//IPDaftar Hitam
function ipBlack(type) {
    if (type == undefined) {
        create_l = layer.open({
            type: 1,
            title: "ManajemenIPDaftar Hitam",
            area: ['500px', '500px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="tab_list"><div class="tab_block active">IPv4Daftar Hitam</div><div class="tab_block">IPv6Daftar Hitam</div></div>\
                <div class="pd15 ipv4_block">\
                    <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                        <input class="bt-input-text" name="start_ip" type="text" value="" style="width:150px;margin-right:15px;margin-left:5px" placeholder="AwalIPAlamat">\
                        <input class="bt-input-text mr5" name="end_ip" type="text" style="width:150px;margin-left:5px;margin-right:20px" placeholder="SelesaiIPAlamat">\
                        <button class="btn btn-success btn-sm va0 pull-right" onclick="addIpBlack();">Tambah</button>\</div>\
                    <div class="divtable">\
                    <div id="ipBlack" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
                    <table class="table table-hover" style="border:none">\
                        <thead>\
                            <tr>\
                                <th>AwalIP</th>\
                                <th>SelesaiIP</th>\
                                <th style="text-align: right;">Operasi</th>\
                            </tr>\
                        </thead>\
                        <tbody id="ip_black_con" class="gztr"></tbody>\
                    </table>\
                    </div>\
                    <div style="width:100%" class="mt10">\
                        <button class="btn btn-success btn-sm va0 mr5 mt10" onclick="fileInput(\'ip_black\')" >Impor</button>\
                        <button class="btn btn-success btn-sm va0 mt10" onclick="outputData(\'ip_black\')">Ekspor</button>\
                    </div>\
                </div>\
                <ul class="help-info-text c7 ptb10">\
                    <li>dalam daftar hitamIPSegmen akan dilarang akses,IPKecuali yang sudah ada di daftar putih</li>\
                </ul>\
            </div>\
            <div class="pd15 ipv6_block">\
                <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                    <input class="bt-input-text" name="ipv6_address" type="text" style="width:380px;margin-right:15px;margin-left:5px" placeholder="ipv6Alamat">\
                    <button class="btn btn-success btn-sm va0 btn_add_ipv6" style="margin-left:15px;">Tambah</button>\
                </div>\
                <div class="divtable">\
                    <div id="ipv6_black" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
                        <table class="table table-hover" style="border:none">\
                            <thead><tr><th>IPv6Alamat</th><th style="text-align: right;">Operasi</th></tr></thead>\
                            <tbody id="ipv6_black_con" class="gztr"></tbody>\
                        </table>\
                    </div>\
                </div>\
                <ul class="help-info-text c7 ptb10">\
                    <li>dalam daftar hitamIPSegmen akan dilarang akses,IPKecuali yang sudah ada di daftar putih</li>\
                </ul>\
            </div>',
            success:function(index,layero){
                $('.tab_list .tab_block').click(function(){
                    $(this).addClass('active').siblings().removeClass('active');
                    if($(this).index() === 0){
                        $('.ipv4_block').show().next().hide();
                        getIpv4Address(function(rdata){
                            var tbody = ''
                            for (var i = 0; i < rdata.length; i++) {
                                tbody += '<tr>\
                                        <td>'+ rdata[i][0].join('.') + '</td>\
                                        <td>'+ rdata[i][1].join('.') + '</td>\
                                        <td class="text-right"><a class="btlink" onclick="removeIpBlack('+ i + ')">Hapus</a></td>\
                                    </tr>'
                            }
                            $("#ip_black_con").html(tbody);
                        });
                    }else{
                        $('.ipv4_block').hide().next().show();
                        getIpv6Address(function(res){
                            var tbody = '',rdata = res;
                            for (var i = 0; i < rdata.length; i++) {
                                tbody += '<tr>\
                                    <td>'+ rdata[i] + '</td>\
                                    <td class="text-right"><a class="btlink" onclick="removeIpv6Black(\''+ rdata[i] + '\')">Hapus</a></td>\
                                </tr>'
                            }
                            $("#ipv6_black_con").html(tbody);
                        });
                    }
                });
                $('.btn_add_ipv6').click(function(){
                    var ipv6 = $('[name="ipv6_address"]').val();
                    addIpv6Req(ipv6, function(res){
                        layer.msg(res.msg,{icon:res.status?1:2});
                        if(res.status){
                            $('[name="ipv6_address"]').val('');
                            $('.tab_list .tab_block:eq(1)').click();
                        }
                    });
                });
                $('.tab_list .tab_block:eq(0)').click();
            }
        });
        tableFixed("ipBlack");
    } else {
        $('.tab_list .tab_block:eq(0)').click();
    }
}

function wafScreen(){

    owPost('waf_srceen', {}, function(data){
        var rdata = $.parseJSON(data.data);

        var end_time = Date.now();
        var cos_time = (end_time/1000) - parseInt(rdata['start_time']);
        var cos_day = parseInt(parseInt(cos_time)/86400);

        var con = '<div class="wavbox alert alert-success" style="margin-right:16px">Total intersepsi<span>'+rdata.total+'</span>Kali</div>';
        con += '<div class="wavbox alert alert-info" style="margin-right:16px">Perlindungan Keamanan<span>'+cos_day+'</span>Hari</div>';

        con += '<div class="screen">\
            <div class="line"><span class="name">POSTPenetrasi</span><span class="val">'+rdata.rules.post+'</span></div>\
            <div class="line"><span class="name">GETPenetrasi</span><span class="val">'+rdata.rules.args+'</span></div>\
            <div class="line"><span class="name">CCSerangan</span><span class="val">'+rdata.rules.cc+'</span></div>\
            <div class="line"><span class="name">JahatUser-Agent</span><span class="val">'+rdata.rules.user_agent+'</span></div>\
            <div class="line"><span class="name">CookiePenetrasi</span><span class="val">'+rdata.rules.cookie+'</span></div>\
            <div class="line"><span class="name">Pemindaian jahat</span><span class="val">'+rdata.rules.scan+'</span></div>\
            <div class="line"><span class="name">JahatHEADPermintaan</span><span class="val">0</span></div>\
            <div class="line"><span class="name">URIIntersepsi kustom</span><span class="val">'+rdata.rules.url+'</span></div>\
            <div class="line"><span class="name">URIProteksi</span><span class="val">'+rdata.rules.args+'</span></div>\
            <div class="line"><span class="name">Unggah file jahat</span><span class="val">'+rdata.rules.upload_ext+'</span></div>\
            <div class="line"><span class="name">Ekstensi yang dilarang</span><span class="val">'+rdata.rules.path+'</span></div>\
            <div class="line"><span class="name">LarangPHPSkrip</span><span class="val">'+rdata.rules.php_path+'</span></div>\
            </div>';

        con += '<div style="width:660px;"><ul class="help-info-text c7">\
            <li>Setelah mematikan firewall di sini,Semua situs akan kehilangan perlindungan</li>\
            <li>Firewall situs akan membuatnginxAda sedikit penurunan performa(&lt;5% 10CHasil tes konkurensi statis)</li>\
            <li>Firewall situs terutama menargetkan serangan penetrasi situs,Sementara tidak memiliki fitur penguatan sistem</li>\
            </ul></div>';

        $(".soft-man-con").html(con);
    });
}

function wafGloablRefresh(time){
    setTimeout(function(){
        wafGloabl();
    }, time);
}

function wafGloabl(){
    owPost('waf_conf', {}, function(data){
        var rdata = $.parseJSON(data.data);

        var con = '<div class="divtable">\
            <table class="table table-hover waftable">\
                <thead><tr><th width="18%">Nama</th>\
                <th width="44%">Deskripsi</th>\
                <th width="10%">Respons</th>\
                <th style="text-align: center;" width="10%">Status</th>\
                <th style="text-align: right;">Operasi</th></tr>\
                </thead>\
                <tbody>\
                    <tr><td>Pertahanan CC</td>\
                        <td>PertahananCCSerangan，Parameter pertahanan spesifik silakan sesuaikan di konfigurasi situs</td>\
                        <td><a class="btlink" onclick="setRequestCode(\'cc\','+rdata.cc.status+')">'+rdata.cc.status+'</a></td>\
                        <td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closecc" type="checkbox" '+(rdata.cc.open ? 'checked' : '')+'>\
                            <label class="btswitch-btn" for="closecc" onclick="setObjOpen(\'cc\')"></label></div>\
                        </td>\
                        <td class="text-right"><a class="btlink" onclick="setCcRule('+rdata.cc.cycle+','+rdata.cc.limit+','+rdata.cc.endtime+',\'undefined\','+rdata.cc.increase+')">Aturan awal</a></td>\
                    </tr>\
                    <tr>\
                        <td>Toleransi kejahatan</td>\
                        <td>Blokir permintaan jahat beruntun，Silakan sesuaikan ambang toleransi di konfigurasi situs</td>\
                        <td><a class="btlink" onclick="setRequestCode(\'cc\','+ rdata.cc.status + ')">' + rdata.cc.status + '</a></td>\
                        <td style="text-align: center;">--</td>\
                        <td class="text-right"><a class="btlink" onclick="setRetry('+ rdata.retry.retry_cycle + ',' + rdata.retry.retry + ',' + rdata.retry.retry_time + ')">Aturan awal</a></td>\
                    </tr>\
                    <tr>\
                        <td>Verifikasi keamanan paksa</td>\
                        <td>'+rdata.safe_verify.ps+'</td>\
                        <td>--</td>\
                        <td style="text-align: center;"><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="close_safe_verify" type="checkbox" '+(rdata.safe_verify.open ? 'checked' : '')+'>\
                            <label class="btswitch-btn" for="close_safe_verify" onclick="setObjOpen(\'safe_verify\')"></label></div>\
                        </td>\
                        <td class="text-right"><a class="btlink" onclick="setSafeVerify('+ rdata.safe_verify.auto + ',' + rdata.safe_verify.cpu + ',' + rdata.safe_verify.time + ',\'' + rdata.safe_verify.mode + '\')">Atur</a> | <a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/safe_js.html\')">Konten respons</a></td>\
                    </tr>\
                    <tr>\
                        <td>Filter URI GET</td>\
                        <td>'+ rdata.get.ps + '</td>\
                        <td><a class="btlink" onclick="setRequestCode(\'get\',' + rdata.get.status + ')">' + rdata.get.status + '</a></td>\
                        <td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closeget" type="checkbox" '+ (rdata.get.open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closeget" onclick="setObjOpen(\'get\')"></label>\
                        </div></td>\
                        <td class="text-right"><a class="btlink" onclick="setObjConf(\'url\')">Aturan</a> | <a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/get.html\')">Konten respons</a></td>\
                    </tr>\
                    <tr>\
                        <td>GET-Filter Parameter</td><td>'+ rdata.get.ps + '</td><td><a class="btlink" onclick="setRequestCode(\'get\',' + rdata.get.status + ')">' + rdata.get.status + '</a></td><td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closeget" type="checkbox" '+ (rdata.get.open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closeget" onclick="setObjOpen(\'get\')"></label>\
                        </div></td><td class="text-right"><a class="btlink" onclick="setObjConf(\'args\')">Aturan</a> | <a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/get.html\')">Konten respons</a></td>\
                    </tr>\
                    <tr>\
                        <td>Filter POST</td><td>'+ rdata.post.ps + '</td><td><a class="btlink" onclick="setRequestCode(\'post\',' + rdata.post.status + ')">' + rdata.post.status + '</a></td><td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closepost" type="checkbox" '+ (rdata.post.open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closepost" onclick="setObjOpen(\'post\')"></label>\
                        </div></td><td class="text-right"><a class="btlink" onclick="setObjConf(\'post\')">Aturan</a> | <a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/post.html\')">Konten respons</a></td>\
                    </tr>\
                    <tr>\
                        <td>Filter User-Agent</td><td>'+ rdata['user-agent'].ps + '</td><td><a class="btlink" onclick="setRequestCode(\'user-agent\',' + rdata['user-agent'].status + ')">' + rdata['user-agent'].status + '</a></td><td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closeua" type="checkbox" '+ (rdata['user-agent'].open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closeua" onclick="setObjOpen(\'user-agent\')"></label>\
                        </div></td><td class="text-right"><a class="btlink" onclick="setObjConf(\'user_agent\')">Aturan</a> | <a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/user_agent.html\')">Konten respons</a></td>\
                    </tr>\
                    <tr>\
                        <td>Filter Cookie</td><td>'+ rdata.cookie.ps + '</td><td><a class="btlink" onclick="setRequestCode(\'cookie\',' + rdata.cookie.status + ')">' + rdata.cookie.status + '</a></td><td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closecookie" type="checkbox" '+ (rdata.cookie.open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closecookie" onclick="setObjOpen(\'cookie\')"></label>\
                        </div></td><td class="text-right"><a class="btlink" onclick="setObjConf(\'cookie\')">Aturan</a> | <a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/cookie.html\')">Konten respons</a></td>\
                    </tr>\
                    <tr>\
                        <td>Pemindai umum</td><td>'+ rdata.scan.ps + '</td><td><a class="btlink" onclick="setRequestCode(\'scan\',' + rdata.scan.status + ')">' + rdata.scan.status + '</a></td><td><div class="ssh-item">\
                            <input class="btswitch btswitch-ios" id="closescan" type="checkbox" '+ (rdata.scan.open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closescan" onclick="setObjOpen(\'scan\')"></label>\
                        </div></td><td class="text-right"><a class="btlink" onclick="scanRule()">Atur</a></td>\
                    </tr>\
                    <tr>\
                        <td>URLDaftar Putih</td><td>Semua aturan terhadapURLDaftar putih tidak valid</td><td style="text-align: center;">--</td>\
                        <td style="text-align: center;">--</td>\
                        <td class="text-right"><a class="btlink" onclick="urlWhite()">Atur</a></td>\
                    </tr>\
                    <tr>\
                        <td>IPDaftar Putih</td><td>Semua aturan terhadapIPDaftar putih tidak valid</td><td style="text-align: center;">--</td>\
                        <td style="text-align: center;">--</td>\
                        <td class="text-right"><a class="btlink" onclick="ipWhite()">Atur</a></td>\
                    </tr>\
                    <tr>\
                        <td>IPDaftar Hitam</td><td>yang dilarang aksesIP</td><td><a class="btlink" onclick="setRequestCode(\'cc\','+ rdata.cc.status + ')">' + rdata.cc.status + '</a></td>\
                        <td style="text-align: center;">--</td>\
                        <td class="text-right"><a class="btlink" onclick="ipBlack()">Atur</a></td>\
                    </tr>\
                    <tr>\
                        <td>Lainnya</td><td>'+ rdata.other.ps + '</td><td>--</td>\
                        <td style="text-align: center;">--</td>\
                        <td class="text-right"><a class="btlink" href="javascript:;" onclick="onlineEditFile(0,\''+rdata['reqfile_path']+'/other.html\')">Konten respons</a></td>\
                    </tr>\
                </tbody>\
            </table>\
            </div>';


        con += '<div style="width:645px;margin-top:10px;"><ul class="help-info-text c7">\
            <li>Wariskan: Pengaturan global akan diwariskan otomatis ke konfigurasi situs</li>\
            <li>Prioritas: IPDaftar Putih>IPDaftar Hitam>URLDaftar Putih>URLDaftar Hitam>Pertahanan CC>User-Agent>URIFilter>URLParameter>Cookie>POST</li>\
            </ul></div>';
        $(".soft-man-con").html(con);
    });
}

//Kembalicss
function back_css(v) {
    if (v > 0) {
        return 'tipsval'
    }
    else {
        return 'tipsval tipsvalnull'
    }
}

function html_encode(value) {
    return $('<div></div>').html(value).text();
}

function html_decode(value) {
    return $('<div></div>').text(value).html();
}

//Tambah aturan filter situs
function addSiteRule(siteName, ruleName) {
    var pdata = {
        ruleValue: $("input[name='site_rule_value']").val(),
        siteName: siteName,
        ruleName: ruleName
    }

    if (pdata['ruleValue'] == '') {
        layer.msg('Aturan filter tidak boleh kosong');
        $("input[name='site_rule_value']").focus();
        return;
    }

    owPost('add_site_rule', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
                siteRuleAdmin(siteName, ruleName, 1);
            },1000);
        }
    });
}

//Hapus aturan filter situs
function removeSiteRule(siteName, ruleName, index) {
    var pdata = {
        index: index,
        siteName: siteName,
        ruleName: ruleName
    }

    owPost('remove_site_rule', pdata, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            if (ruleName == 'url_tell') {
                site_url_tell(siteName, 1);
                return;
            }

            if (ruleName == 'url_rule') {
                site_url_rule(siteName, 1);
                return;
            }

            setTimeout(function(){
                siteRuleAdmin(siteName, ruleName, 1);
            },1000);
        }
    });
}

//Manajemen aturan situs
function siteRuleAdmin(siteName, ruleName, type) {
    var placeho = '';
    var ps = '';
    var title = '';
    switch (ruleName) {
        case 'disable_php_path':
            placeho = 'Alamat URI,Mendukung regex';
            ps = '<li>Jangan sertakan di siniURIParameter,Umumnya untuk direktoriURL,Contoh：/admin</li>'
            title = 'Larang jalankanPHPdariURLAlamat'
            break;
        case 'disable_path':
            placeho = 'Alamat URI,Mendukung regex';
            ps = '<li>Jangan sertakan di siniURIParameter,Umumnya untuk direktoriURL,Contoh：/admin</li>'
            title = 'yang dilarang aksesURLAlamat'
            break;
        case 'disable_ext':
            placeho = 'Ekstensi，Tidak mengandung titik(.)，Contoh：sql';
            ps = '<li>Isi langsung ekstensi yang dilarang akses，Misalnya saya ingin melarang akses*.sqlFile：sql</li>'
            title = 'Ekstensi yang dilarang akses'
            break;
        case 'disable_upload_ext':
            placeho = 'Ekstensi，Tidak mengandung titik(.)，Contoh：sql';
            ps = '<li>Isi langsung ekstensi yang dilarang akses，Misalnya saya ingin melarang unggahan*.phpFile：php</li>'
            title = 'Tipe file yang dilarang unggah'
            break;
    }
    if (type == undefined) {
        create_l = layer.open({
            type: 1,
            title: "Manajemen aturan filter situs【" + title + "】",
            area: ['500px', '500px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="pd15">\
                <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                    <input class="bt-input-text" name="site_rule_value" type="text" value="" style="width:400px;margin-right:15px;margin-left:5px" placeholder="'+ placeho + '">\
                    <button class="btn btn-success btn-sm va0 pull-right" onclick="addSiteRule(\''+ siteName + '\',\'' + ruleName + '\');">Tambah</button>\</div>\
                <div class="divtable">\
                <div id="siteRuleAdmin" class="siteRuleAdmin" style="max-height:273px;overflow:auto;border:#ddd 1px solid">\
                <table class="table table-hover" style="border:none">\
                    <thead>\
                        <tr>\
                            <th>Aturan</th>\
                            <th style="text-align: right;">Operasi</th>\
                        </tr>\
                    </thead>\
                    <tbody id="site_rule_admin_con" class="gztr"></tbody>\
                </table>\
                </div>\
            </div>\
            <ul class="help-info-text c7 ptb10">\
                <li>Selain regex, nilai aturan tidak peka huruf besar-kecil,Disarankan gunakan huruf kecil semua</li>'+ ps + '\
            </ul></div>'
        });
        tableFixed("siteRuleAdmin");
    }

    owPost('get_site_rule', { siteName: siteName, ruleName: ruleName }, function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        var tbody = ''
        for (var i = 0; i < rdata.length; i++) {
            tbody += '<tr>\
                    <td>'+ rdata[i] + '</td>\
                    <td class="text-right"><a class="btlink" onclick="removeSiteRule(\''+ siteName + '\',\'' + ruleName + '\',' + i + ')">Hapus</a></td>\
                </tr>'
        }
        $("#site_rule_admin_con").html(tbody);
    });
}

//CDN-HeaderKonfigurasi
function cdnHeader(siteName, type) {
    if (type == undefined) {
        create_l = layer.open({
            type: 1,
            title: "Manajemen situs【" + siteName + "】CDN-Headers",
            area: ['500px', '500px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="pd15">\
                <div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px">\
                    <input class="bt-input-text" name="cdn_header_key" type="text" value="" style="width:400px;margin-right:15px;margin-left:5px" placeholder="Nama Header">\
                    <button class="btn btn-success btn-sm va0 pull-right" onclick="addCdnHeader(\''+ siteName + '\');">Tambah</button>\</div>\
                <div class="divtable">\
                <div id="cdnHeader" style="max-height:300px;overflow:auto;border:#ddd 1px solid">\
                <table class="table table-hover" style="border:none">\
                    <thead>\
                        <tr>\
                            <th>header</th>\
                            <th style="text-align: right;">Operasi</th>\
                        </tr>\
                    </thead>\
                    <tbody id="cdn_header_con" class="gztr"></tbody>\
                </table>\
            </div>\
            </div>\
            <ul class="help-info-text c7 ptb10">\
                <li>Firewall akan mencoba di atasheadermendapatkan klien dariIP</li>\
            </ul></div>'
        });
        tableFixed("cdnHeader");
    }

    owPost('get_site_config_byname', { siteName: siteName }, function(data){
        var tmp = $.parseJSON(data.data);
        var t1 = tmp.data;
        var rdata = t1['cdn_header'];
        var tbody = ''
        for (var i = 0; i < rdata.length; i++) {
            tbody += '<tr>\
                    <td>'+ rdata[i] + '</td>\
                    <td class="text-right"><a class="btlink" onclick="removeCdnHeader(\''+ siteName + '\',\'' + rdata[i] + '\')">Hapus</a></td>\
                </tr>'
        }
        $("#cdn_header_con").html(tbody);
    });
}

//TambahCDN-Header
function addCdnHeader(siteName) {
    var pdata = {
        cdn_header: $("input[name='cdn_header_key']").val(),
        siteName: siteName
    }

    if (pdata['cdn_header'] == '') {
        layer.msg('Header Tidak boleh kosong');
        $("input[name='cdn_header_key']").focus();
        return;
    }

    owPost('add_site_cdn_header', pdata, function(data){
        var rdata = $.parseJSON(data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
                cdnHeader(siteName, 1);
            },1000);
        }
    });
}

 //HapusCDN-Header
function removeCdnHeader(siteName, cdn_header_key) {
    owPost('remove_site_cdn_header', { siteName: siteName, cdn_header: cdn_header_key }, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.status) {
            setTimeout(function(){
                cdnHeader(siteName, 1);
            },1000);
        }
    });
}

//Atur fitur pertahanan situs
function setSiteObjState(siteName, obj) {
    // var loadT = layer.msg('Sedang diproses，Silakan tunggu..', { icon: 16, time: 0 });
    owPost('set_site_obj_open', { siteName: siteName, obj: obj } , function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        setTimeout(function(){
            siteWafConfig(siteName, 1);
            // siteConfig();
        },1000);
    });
    // $.post('/plugin?action=a&name=btwaf&s=set_site_obj_open', { siteName: siteName, obj: obj }, function (rdata) {
    //     layer.close(loadT);
    //     site_waf_config(siteName, 1);
    //     siteconfig();
    //     layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    // });
}


//Pengaturan aturan situs
function setSiteObjConf(siteName, ruleName, type) {
    if (type == undefined) {
        create_l = layer.open({ 
            type: 1,
            title: "Edit situs【" + siteName + "】Aturan【" + ruleName + "】",
            area: ['700px', '530px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div class="pd15">\
                <div class="divtable">\
                <div id="SetSiteObjConf" class="table_head_fix" style="max-height:375px;overflow:auto;border:#ddd 1px solid">\
                <table class="table table-hover" style="border:none">\
                    <thead>\
                        <tr>\
                            <th width="450">Aturan</th>\
                            <th>Penjelasan</th>\
                            <th style="text-align: right;">Status</th>\
                        </tr>\
                    </thead>\
                    <tbody id="set_site_obj_conf_con" class="gztr"></tbody>\
                </table>\
                </div>\
            </div>\
            <ul class="help-info-text c7 ptb10">\
                <li>Di sini mewarisi aturan yang aktif di pengaturan global</li>\
                <li>Pengaturan di sini hanya berlaku untuk situs saat ini</li>\
            </ul></div>'
        });
        tableFixed("SetSiteObjConf");
    }

    getRuleByName(ruleName, function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        var tbody = '';
        var tbody = '';
        for (var i = 0; i < rdata.length; i++) {
            if (rdata[i][0] == -1) continue;
            tbody += '<tr>\
                    <td>'+ rdata[i][1] + '</td>\
                    <td>'+ rdata[i][2] + '</td>\
                    <td style="text-align: right;">\
                        <div class="pull-right"><input class="btswitch btswitch-ios" id="close_'+ i + '" type="checkbox" ' + (rdata[i][0] ? 'checked' : '') + '>\
                        <label class="btswitch-btn" for="close_'+ i + '" style="width:2em;height:1.2em;margin-bottom: 0" for="closeua_' + i + '" onclick="set_site_rule_state(\'' + siteName + '\',\'' + ruleName + '\',' + i + ')"></label></div>\
                    </td>\
                </tr>'
        }
        $("#set_site_obj_conf_con").html(tbody)
    });
}

//Pengaturan situs
function siteWafConfig(siteName, type) {
    if (type == undefined) {
        create_2 = layer.open({
            type: 1,
            title: "Konfigurasi situs【" + siteName + "】",
            area: ['700px', '500px'],
            closeBtn: 1,
            shadeClose: false,
            content: '<div id="s_w_c"></div>'
        });
    }

    owPost('get_site_config_byname', { siteName: siteName }, function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = tmp.data;
        nginx_config = rdata;
        var con = '<div class="pd15">\
                <div class="lib-con-title">\
                    <span>Sakelar firewall situs</span>\
                    <div class="ssh-item" style="margin-right:20px;">\
                        <input class="btswitch btswitch-ios" id="closewaf_open" type="checkbox" '+ (rdata.open ? 'checked' : '') + '>\
                        <label class="btswitch-btn" for="closewaf_open" onclick="setSiteObjState(\''+ siteName + '\',\'open\')" style="width:2.4em;height:1.4em;margin-bottom: 0"></label>\
                    </div>\
                </div>\
                <div class="lib-con">\
                    <div class="divtable">\
                        <table class="table table-hover waftable">\
                            <thead>\
                                <tr>\
                                    <th>Nama</th>\
                                    <th>Deskripsi</th>\
                                    <th width="80">Status</th>\
                                    <th style="text-align: right;">Operasi</th>\
                                </tr>\
                            </thead>\
                            <tbody>\
                                <tr>\
                                    <td>Pertahanan CC</td>\
                                    <td><font style="color:red;">'+ rdata.cc.cycle + '</font> dalam detik,Minta yang samaURIKumulatif melebihi <font style="color:red;">' + rdata.cc.limit + '</font> Kali,BlokirIP <font style="color:red;">' + rdata.cc.endtime + '</font> Detik</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closecc" type="checkbox" '+ (rdata.cc.open ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closecc" onclick="setSiteObjState(\''+ siteName + '\',\'cc\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="setCcRule('+ rdata.cc.cycle + ',' + rdata.cc.limit + ',' + rdata.cc.endtime + ',\'' + siteName + '\',' + rdata.cc.increase + ')">Atur</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Pengaturan toleransi kejahatan</td>\
                                    <td><font style="color:red;">'+ rdata.retry.retry_cycle + '</font> dalam detik,Kumulatif melebihi <font style="color:red;">' + rdata.retry.retry + '</font> Kali permintaan jahat,BlokirIP <font style="color:red;">' + rdata.retry.retry_time + '</font> Detik</td>\
                                    <td style="text-align: left;">&nbsp;&nbsp;--</td>\
                                    <td class="text-right"><a class="btlink" onclick="setRetry('+ rdata.retry.retry_cycle + ',' + rdata.retry.retry + ',' + rdata.retry.retry_time + ',\'' + siteName + '\')">Atur</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Filter URI GET</td>\
                                    <td>'+ rdata.get.ps + '</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closeget" type="checkbox" '+ (rdata.get ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closeget" onclick="setSiteObjState(\''+ siteName + '\',\'get\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="setSiteObjConf(\''+ siteName + '\',\'url\')">Aturan</a></td>\
                                </tr>\
                                <td>GET-Filter Parameter</td>\
                                    <td>'+ rdata.get.ps + '</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closeargs" type="checkbox" '+ (rdata.get ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closeargs" onclick="setSiteObjState(\''+ siteName + '\',\'get\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="setSiteObjConf(\''+ siteName + '\',\'args\')">Aturan</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Filter POST</td>\
                                    <td>'+ rdata.post.ps + '</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closepost" type="checkbox" '+ (rdata.post ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closepost" onclick="setSiteObjState(\''+ siteName + '\',\'post\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="setSiteObjConf(\''+ siteName + '\',\'post\')">Aturan</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Filter User-Agent</td>\
                                    <td>'+ rdata['user-agent'].ps + '</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closeua" type="checkbox" '+ (rdata['user-agent'] ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closeua" onclick="setSiteObjState(\''+ siteName + '\',\'user-agent\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="setSiteObjConf(\''+ siteName + '\',\'user_agent\')">Aturan</a></td>\
                                </tr>\
                                 <tr>\
                                    <td>Filter Cookie</td>\
                                    <td>'+ rdata.cookie.ps + '</td>\
                                    <td>\
                                    <div class="ssh-item" style="margin-left:0">\
                                        <input class="btswitch btswitch-ios" id="closecookie" type="checkbox" '+ (rdata.cookie ? 'checked' : '') + '>\
                                        <label class="btswitch-btn" for="closecookie" onclick="setSiteObjState(\''+ siteName + '\',\'cookie\')"></label>\
                                    </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="setSiteObjConf(\''+ siteName + '\',\'cookie\')">Aturan</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Pemindai umum</td><td>'+ rdata.scan.ps + '</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closescan" type="checkbox" '+ (rdata.scan ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closescan" onclick="setSiteObjState(\''+ siteName + '\',\'scan\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="scanRule()">Atur</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Gunakan CDN</td>\
                                    <td>Situs ini menggunakanCDN,Aktifkan untuk mendapatkan klien dengan benarIP</td>\
                                    <td>\
                                        <div class="ssh-item" style="margin-left:0">\
                                            <input class="btswitch btswitch-ios" id="closecdn" type="checkbox" '+ (rdata.cdn ? 'checked' : '') + '>\
                                            <label class="btswitch-btn" for="closecdn" onclick="setSiteObjState(\''+ siteName + '\',\'cdn\')"></label>\
                                        </div>\
                                    </td>\
                                    <td class="text-right"><a class="btlink" onclick="cdnHeader(\''+ siteName + '\')">Atur</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Larang ekstensi</td>\
                                    <td>Larang akses ekstensi tertentu</td>\
                                    <td style="text-align: left;">&nbsp;&nbsp;--</td>\
                                    <td class="text-right"><a class="btlink" onclick="siteRuleAdmin(\''+ siteName + '\',\'disable_ext\')">Atur</a></td>\
                                </tr>\
                                <tr>\
                                    <td>Tipe file yang dilarang unggah</td>\
                                    <td>Larang unggah tipe file tertentu</td>\
                                    <td style="text-align: left;">&nbsp;&nbsp;--</td>\
                                    <td class="text-right"><a class="btlink" onclick="siteRuleAdmin(\''+ siteName + '\',\'disable_upload_ext\')">Atur</a></td>\
                                </tr>\
                            </tbody>\
                        </table>\
                    </div>\
                </div>\
                <ul class="help-info-text c7">\
                    <li>Catatan: Sebagian besar konfigurasi di sini,Hanya berlaku untuk situs saat ini!</li>\
                </ul>\
            </div>';
        $("#s_w_c").html(con);
    });
}



function wafSite(){
    owPost('get_site_config', {}, function(data){
        var tmp = $.parseJSON(data.data);
        var rdata = $.parseJSON(tmp.data);
        var tbody = '';
        var i = 0;
        $.each(rdata, function (k, v) {
            i += 1;
            tbody += '<tr>\
                    <td><a onclick="siteWafConfig(\''+ k + '\')" class="sitename btlink" title="' + k + '">' + k + '</a></td>\
                    <td><input onclick="setSiteObjState(\''+ k + '\',\'get\')" type="checkbox" ' + (v.get ? 'checked' : '') + '><span class="' + back_css(v.total[1].value) + '" title="IntersepsiGETJumlah penetrasi:' + v.total[1].value + '">' + v.total[1].value + '</span></td>\
                    <td><input onclick="setSiteObjState(\''+ k + '\',\'post\')"  type="checkbox" ' + (v.post ? 'checked' : '') + '><span class="' + back_css(v.total[0].value) + '"  title="IntersepsiPOSTJumlah penetrasi:' + v.total[0].value + '">' + v.total[0].value + '</span></td>\
                    <td><input onclick="setSiteObjState(\''+ k + '\',\'user-agent\')"  type="checkbox" ' + (v['user-agent'] ? 'checked' : '') + '><span class="' + back_css(v.total[3].value) + '" title="Intersepsi jahatUser-AgentJumlah:' + v.total[3].value + '">' + v.total[3].value + '</span></td>\
                    <td><input onclick="setSiteObjState(\''+ k + '\',\'cookie\')"  type="checkbox" ' + (v.cookie ? 'checked' : '') + '><span class="' + back_css(v.total[4].value) + '" title="IntersepsiCookieJumlah penetrasi:' + v.total[4].value + '">' + v.total[4].value + '</span></td>\
                    <td><input onclick="setSiteObjState(\''+ k + '\',\'cdn\')"  type="checkbox" ' + (v.cdn ? 'checked' : '') + '></td>\
                    <td><input onclick="setSiteObjState(\''+ k + '\',\'cc\')"  type="checkbox" ' + (v.cc.open ? 'checked' : '') + '><span class="' + back_css(v.total[2].value) + '" title="IntersepsiCCJumlah serangan:' + v.total[2].value + '">' + v.total[2].value + '</span></td>\
                    <td>\
                        <div class="ssh-item" style="margin-left:0">\
                            <input class="btswitch btswitch-ios" id="closeget_'+ i + '" type="checkbox" ' + (v.open ? 'checked' : '') + '>\
                            <label class="btswitch-btn" for="closeget_'+ i + '" onclick="setSiteObjState(\'' + k + '\',\'open\')"></label>\
                        </div>\
                    </td>\
                    <td class="text-right"><a onclick="wafLogs(\''+ k + '\')" class="btlink ' + (v.log_size > 0 ? 'dot' : '') + '">Log</a> </td>\
                </tr>';
            //| <a onclick="siteWafConfig(\'' + k + '\')" class="btlink">Atur</a>
        });

        var con = '<div class="lib-box">\
                    <div class="lib-con">\
                        <div class="divtable">\
                        <div id="siteCon_fix" style="max-height:580px; overflow:auto;border:#ddd 1px solid">\
                        <table class="table table-hover waftable" style="border:none">\
                            <thead>\
                                <tr>\
                                    <th>Situs</th>\
                                    <th>GET</th>\
                                    <th>POST</th>\
                                    <th>UA</th>\
                                    <th>Cookie</th>\
                                    <th title="Situs ini menggunakanCDNatau silakan centang saat menggunakan proxy lainnya">CDN</th>\
                                    <th>Pertahanan CC</th>\
                                    <th>Status</th>\
                                    <th style="text-align: right;">Operasi</th>\
                                </tr>\
                            </thead>\
                            <tbody>'+ tbody + '</tbody>\
                        </table>\
                        </div>\
                        </div>\
                    </div>\
            </div>';
        $(".soft-man-con").html(con);
        tableFixed("siteCon_fix");
    });
}


function wafAreaLimitRender(){
    function keyVal(obj){
        var str = [];
        $.each(obj, function (index, item) {
            if (item == 1) {
                if (index == 'allsite') index = 'Semua situs';
                if (index == 'Luar Negeri') index = 'Wilayah di luar China Daratan (Termasuk [Hong Kong, Macau, Taiwan])';
                if (index == 'China') index = 'China Daratan (Tidak termasuk [Hong Kong, Macau, Taiwan])';
                str.push(index);
            }
        });
        return str.toString();
    }
    owPost('get_area_limit', {}, function(rdata) {
        var rdata = $.parseJSON(rdata.data);
        if (!rdata.status) {
            layer.msg(rdata.msg, { icon: 2, time: 2000 });
            return;
        }

        var list = '';
        var rlist = rdata.data;

        for (var i = 0; i < rlist.length; i++) {
            var op = '';
            var type = rlist[i]['types'] === 'refuse' ? 'Intersepsi' : 'Hanya izinkan';
            var region_str = keyVal(rlist[i]['region']);
            var site_str = keyVal(rlist[i]['site']);

            op += '<a  data-id="'+i+'" href="javascript:;" class="area_limit_del btlink">Hapus</a>';

            list += '<tr>';
            list += '<td><span class="overflow_hide" style="width: 303px;" title="'+region_str+'"">' + region_str + '</span></td>';
            list += '<td>' + site_str + '</td>';
            list += '<td>' + type + '</td>';
        
            list += '<td class="text-right">' + op + '</td>';
            list += '</tr>';
        }

        $('#con_list tbody').html(list);
        $('.area_limit_del').click(function(){
            var data_id = $(this).data('id');

            var site = [],region = [];
            $.each(rlist[data_id]['site'], function (index, item) {
                site.push(index);
            });
            $.each(rlist[data_id]['region'], function (index, item) {
                region.push(index);
            });

            var type = rlist[data_id]['types'];

            owPost('del_area_limit', {
                site:site.toString(),
                region:region.toString(),
                types:type,
            }, function(rdata) {
                var rdata = $.parseJSON(rdata.data);
                showMsg(rdata.msg, function(){
                    if (rdata.status){
                        wafAreaLimit();
                    }
                },{ icon: rdata.status ? 1 : 2 });
            });
        });
    });
}

function wafAreaLimitSwitch(){
    owPostN('waf_conf', {}, function(data){
        var rdata = $.parseJSON(data.data);
        if (rdata['area_limit']){
            $('#area_limit_switch').prop('checked', true);
        } else{
            $('#area_limit_switch').prop('checked',false);
        }
    });
}

function setWafAreaLimitSwitch(){
    var area_limit_switch = $('#area_limit_switch').prop('checked');
    // console.log(area_limit_switch);
    var area_limit = 'off';
    if (!area_limit_switch){
        area_limit = 'on';
    }
    owPostN('area_limit_switch', {'area_limit': area_limit}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}

// Batasan wilayah
function wafAreaLimit(){
    var con = '<div class="safe bgw">\
            <button id="create_area_limit" class="btn btn-success btn-sm" type="button" style="margin-right: 5px;">Tambah batasan wilayah</button>\
            <input class="btswitch btswitch-ios" id="area_limit_switch" type="checkbox">\
            <label class="btswitch-btn" for="area_limit_switch" onclick="setWafAreaLimitSwitch();" style="display: inline-flex;line-height:38px;margin-left: 4px;float: right;"></label>\
            <div class="divtable mtb10">\
                <div class="tablescroll">\
                    <table id="con_list" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0" style="border: 0 none;">\
                    <thead><tr>\
                    <th>Wilayah</th>\
                    <th>Situs</th>\
                    <th>Tipe</th>\
                    <th style="text-align:right;">Operasi</th></tr></thead>\
                    <tbody></tbody></table>\
                </div>\
            </div>\
        </div>';
    $(".soft-man-con").html(con);
    wafAreaLimitRender();
    wafAreaLimitSwitch();

    $('#create_area_limit').click(function(){
        var site_list;
        var area_list;
        var site_length = 0;
        layer.open({
            type: 1,
            title: 'Tambah batasan wilayah',
            area: ['450px','280px'],
            closeBtn: 1,
            btn: ['Tambah', 'Batal'],
            content: '<div class="waf-form pd20">\
                <div class="line">\
                    <span class="tname">Tipe</span>\
                    <div class="info-r c4">\
                        <select name="type" class="bt-input-text" style="width:230px">\
                            <option value="refuse" selected="">Intersepsi</option>\
                            <option value="accept">Hanya izinkan</option>\
                        </select>\
                    </div>\
                </div>\
                <div class="line">\
                    <span class="tname">Situs</span>\
                    <div class="info-r">\
                        <div id="site_list"></div>\
                    </div>\
                </div>\
                <div class="line">\
                    <span class="tname">Wilayah</span>\
                    <div class="info-r" id="area_list"></div>\
                </div>\
            </div>',
            success: function (layers, index) {
                document.getElementById('layui-layer' + index).getElementsByClassName('layui-layer-content')[0].style.overflow = 'unset';

                site_list = xmSelect.render({
                    el: '#site_list',
                    language: 'en',
                    tips: 'Silakan pilih situs',
                    empty: 'Data kosong',
                    searchTips: 'Cari situs...',
                    toolbar: {show: true, list: [{name: 'Semua', method: 'ALL'}, {name: 'Kosongkan', method: 'CLEAR'}, {name: 'Balikkan', method: 'REVERSE'}]},
                    paging: true,
                    pageSize: 10,
                    data: [],
                });

                owPostN('get_default_site','', function(rdata){
                    var rdata = $.parseJSON(rdata.data);
                    var rlist = rdata.data.list;


                    var pdata = [];
                    for (var i = 0; i < rlist.length; i++) {
                        var tval = rlist[i];
                        if (tval != 'unset'){
                            var t = {name:rlist[i],value:rlist[i]};
                            pdata.push(t);
                        }
                    }
                    site_length = pdata.length;
                    site_list.update({data:pdata});
                });

                area_list = xmSelect.render({
                    el: '#area_list',
                    language: 'en',
                    tips: 'Silakan pilih wilayah',
                    empty: 'Data kosong',
                    searchTips: 'Cari wilayah...',
                    toolbar: {show: true, list: [{name: 'Semua', method: 'ALL'}, {name: 'Kosongkan', method: 'CLEAR'}, {name: 'Balikkan', method: 'REVERSE'}]},
                    filterable: true,
                    data: [],
                });
                owPostN('get_country','', function(rdata){
                    var rdata = $.parseJSON(rdata.data);
                    var rlist = rdata.data;

                    var pdata = [];
                    for (var i = 0; i < rlist.length; i++) {
                        var tval = rlist[i];
                        if (tval != 'unset'){
                            var t = {name:tval,value:tval};
                            pdata.push(t);
                        }
                    }

                    area_list.update({data:pdata});
                });
            },
            yes: function (indexs) {

                var reg_type = $('select[name="type"]').val();
                var site_val = site_list.getValue('value');
                var area_val = area_list.getValue('value');

                if (area_val.length <1) return layer.msg('Pilih minimal satu wilayah!', { icon: 2 });
                if (site_val.length <1) return layer.msg('Pilih minimal satu situs!', { icon: 2 });

                var site = '';
                if (site_length === site_val.length) {
                    site = 'allsite';
                } else {
                    site = site_val.join();
                }

                var area = area_val.join();
                var region = area.replace('Wilayah di luar China Daratan (Termasuk [Hong Kong, Macau, Taiwan])', 'Luar Negeri')
                    .replace('China Daratan (Tidak termasuk [Hong Kong, Macau, Taiwan])', 'China')
                    .replace('Hong Kong', 'Hong Kong')
                    .replace('Macau', 'Macau')
                    .replace('Taiwan', 'Taiwan');

                owPost('add_area_limit',{
                    site:site,
                    types:reg_type,
                    region:region,
                }, function(rdata){
                    var rdata = $.parseJSON(rdata.data);
                    showMsg(rdata.msg, function(){
                        if (rdata.status){
                            layer.close(indexs);
                            wafAreaLimit();
                        }
                    },{ icon: rdata.status ? 1 : 2 });
                });

            },
        });
    });
}

function wafLogRequest(page){
    var args = {};   
    args['page'] = page;
    args['page_size'] = 10;
    args['site'] = $('select[name="site"]').val();

    var query_date = 'today';
    if ($('#time_choose').attr("data-name") != ''){
        query_date = $('#time_choose').attr("data-name");
    } else {
        query_date = $('#search_time button.cur').attr("data-name");
    }

    args['query_date'] = query_date;
    args['tojs'] = 'wafLogRequest';

    owPost('get_logs_list', args, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        var list = '';
        var data = rdata.data.data;
        if (data.length > 0){
            for(i in data){
                list += '<tr>';
                list += '<td><span class="overflow_hide" style="width:112px;">' + getLocalTime(data[i]['time'])+'</span></td>';
                list += '<td><span class="overflow_hide" style="width:50px;">' + data[i]['domain'] +'</span></td>';
                list += '<td><span class="overflow_hide" style="width:60px;">' + data[i]['ip'] +'</span></td>';
                list += '<td><span class="overflow_hide" style="width:50px;">' + data[i]['uri'] +'</span></td>';// data[i]['uri']
                list += '<td><span class="overflow_hide" style="width:50px;">' + data[i]['rule_name'] +'</span></td>';
                list += '<td><span class="overflow_hide" style="width:200px;">' + entitiesEncode(data[i]['reason']) +'</span></td>';//data[i]['reason']
                list += '<td><a data-id="'+i+'" href="javascript:;" class="btlink details" title="Detail">Detail</a></td>';
                list += '</tr>';
            }
        } else{
             list += '<tr><td colspan="8" style="text-align:center;">Log blokir kosong</td></tr>';
        }
        
        var table = '<div class="tablescroll">\
                            <table id="DataBody" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0" style="border: 0 none;">\
                            <thead><tr>\
                            <th>Waktu</th>\
                            <th>Domain</th>\
                            <th>IP</th>\
                            <th>URI</th>\
                            <th>Nama aturan</th>\
                            <th>Alasan</th>\
                            <th style="text-align:right;">Operasi</th></tr></thead>\
                            <tbody>\
                            '+ list +'\
                            </tbody></table>\
                        </div>\
                        <div id="wsPage" class="dataTables_paginate paging_bootstrap page"></div>';
        $('#ws_table').html(table);
        $('#wsPage').html(rdata.data.page);

        $(".tablescroll .details").click(function(){
            var index = $(this).attr('data-id');
            var res = data[index];
            var ip = res.ip;
            var time = getLocalTime(res.time);
            layer.open({
                type: 1,
                title: "【"+res.domain + "】Detail",
                area: '600px',
                closeBtn: 1,
                shadeClose: false,
                content: '<div class="pd15 lib-box">\
                        <table class="table" style="border:#ddd 1px solid; margin-bottom:10px">\
                        <tbody><tr><th>Waktu</th><td>'+ time + '</td><th>IP Pengguna</th><td><a class="btlink" href="javascript:addIpBlackArgs(\'' + escapeHTML(ip) + '\')" title="Tambah ke daftar hitam">' + escapeHTML(ip) + '</a></td></tr><tr><th>Tipe</th><td>' + escapeHTML(res.method) + '</td><th>Filter</th><td>' + escapeHTML(res.rule_name) + '</td></tr></tbody></table>\
                        <div><b style="margin-left:10px">Alamat URI</b></div>\
                        <div class="lib-con pull-left mt10"><div class="divpre">'+ escapeHTML(res.uri) + '</div></div>\
                        <div><b style="margin-left:10px">User-Agent</b></div>\
                        <div class="lib-con pull-left mt10"><div class="divpre">'+ escapeHTML(res.user_agent) + '</div></div>\
                        <div><b style="margin-left:10px">Aturan filter</b></div>\
                        <div class="lib-con pull-left mt10"><div class="divpre">'+ escapeHTML(res.rule_name) + '</div></div>\
                         <div><b style="margin-left:10px">Reason</b></div>\
                        <div class="lib-con pull-left mt10"><div class="divpre">'+ escapeHTML(res.reason) + '</div></div>\
                    </div>'
            })
        });
    });
}

function wafLogs(){
    var randstr = getRandomString(10);


    var html = '<div>\
                <div style="padding-bottom:10px;">\
                    <span>Situs: </span>\
                    <select class="bt-input-text" name="site" style="margin-left:4px;width:100px;">\
                        <option value="unset">Belum diatur</option>\
                    </select>\
                    <span style="margin-left:10px">Waktu: </span>\
                    <div class="input-group" style="margin-left:10px;width:350px;display: inline-table;vertical-align: top;">\
                        <div id="search_time" class="input-group-btn btn-group-sm">\
                            <button data-name="today" type="button" class="btn btn-default">Hari ini</button>\
                            <button data-name="yesterday" type="button" class="btn btn-default">Kemarin</button>\
                            <button data-name="l7" type="button" class="btn btn-default">Dekat7Hari</button>\
                            <button data-name="l30" type="button" class="btn btn-default">Dekat30Hari</button>\
                        </div>\
                        <span class="last-span"><input data-name="" type="text" id="time_choose" lay-key="1000001_'+randstr+'" class="form-control btn-group-sm" autocomplete="off" placeholder="Waktu kustom" style="display: inline-block;font-size: 12px;padding: 0 10px;height:30px;width: 155px;"></span>\
                    </div>\
                    <div style="float:right;">\
                        <button id="UncoverAll" class="btn btn-success btn-sm" style="padding-left: 5px;padding-right: 5px;">Buka semua blokir</button>\
                        <button id="testRun" class="btn btn-default btn-sm" style="padding-left: 5px;padding-right: 5px;">Tes</button>\
                    </div>\
                </div>\
                <div class="divtable mtb10" id="ws_table"></div>\
            </div>';
    $(".soft-man-con").html(html);
    // wafLogRequest(1);

    $("#UncoverAll").click(function(){
        owPost('clean_drop_ip',{},function(data){
            var rdata = $.parseJSON(data.data);
            var ndata = $.parseJSON(rdata.data);
            if (ndata.status == 0){
                layer.msg("Buka semua blokir berhasil",{icon:1,time:2000,shade: [0.3, '#000']});
            } else{
                layer.msg("Buka semua blokir abnormal:"+ndata.msg,{icon:5,time:2000,shade: [0.3, '#000']});
            }
        });
    });

    //Tesdemo
    $("#testRun").click(function(){
        owPost('test_run',{},function(data){
            var rdata = $.parseJSON(data.data);
            showMsg(rdata.msg, function(){
                wafLogRequest(1);
            },{icon:1,shade: [0.3, '#000']},2000);
        });
    });

    //Rentang tanggal
    laydate.render({
        elem: '#time_choose',
        value:'',
        range:true,
        done:function(value, startDate, endDate){
            if(!value){
                return false;
            }

            $('#search_time button').each(function(){
                $(this).removeClass('cur');
            });

            var timeA  = value.split('-');
            var start = $.trim(timeA[0]+'-'+timeA[1]+'-'+timeA[2])
            var end = $.trim(timeA[3]+'-'+timeA[4]+'-'+timeA[5])
            query_txt = toUnixTime(start + " 00:00:00") + "-"+ toUnixTime(end + " 00:00:00")

            $('#time_choose').attr("data-name",query_txt);
            $('#time_choose').addClass("cur");

            wafLogRequest(1);
        },
    });

    $('#search_time button:eq(0)').addClass('cur');
    $('#search_time button').click(function(){
        $('#search_time button').each(function(){
            if ($(this).hasClass('cur')){
                $(this).removeClass('cur');
            }
        });
        $('#time_choose').attr("data-name",'');
        $('#time_choose').removeClass("cur");

        $(this).addClass('cur');

        wafLogRequest(1);
    });

    owPostN('get_default_site',{},function(rdata){
        $('select[name="site"]').html('');

        var rdata = $.parseJSON(rdata.data);
        var rdata = rdata.data;
        var default_site = rdata["default"];
        var select = '';
        for (var i = 0; i < rdata["list"].length; i++) {
            if (default_site ==  rdata["list"][i]){
                select += '<option value="'+rdata["list"][i]+'" selected>'+rdata["list"][i]+'</option>';
            } else{
                select += '<option value="'+rdata["list"][i]+'">'+rdata["list"][i]+'</option>';
            }
        }
        $('select[name="site"]').html(select);
        wafLogRequest(1);

        $('select[name="site"]').change(function(){
            wafLogRequest(1);
        });
    });

}


function wafOpLogs(){
    var con = '<div class="divtable">\
        <table class="table table-hover waftable" style="color:#fff;">\
            <thead><tr><th width="18%">Nama</th>\
            <th width="44%">Deskripsi</th>\
            <th width="10%">Respons</th>\
            <th style="text-align: center;" width="10%">Status</th>\
            <th style="text-align: right;">Operasi</th></tr>\
            </thead>\
        </table>\
        </div>';    
    $(".soft-man-con").html(con);
}

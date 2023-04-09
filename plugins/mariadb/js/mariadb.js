function myPost(method,args,callback, title){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(toArrayObject(args));
    } else {
        _args = JSON.stringify(args);
    }

    var _title = 'Retrieving...';
    if (typeof(title) != 'undefined'){
        _title = title;
    }

    var loadT = layer.msg(_title, { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'mariadb', func:method, args:_args}, function(data) {
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

function myPostN(method,args,callback, title){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(toArrayObject(args));
    } else {
        _args = JSON.stringify(args);
    }

    var _title = 'Retrieving...';
    if (typeof(title) != 'undefined'){
        _title = title;
    }
    $.post('/plugins/run', {name:'mariadb', func:method, args:_args}, function(data) {
        if(typeof(callback) == 'function'){
            callback(data);
        }
    },'json');
}

function myAsyncPost(method,args){
    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(toArrayObject(args));
    } else {
        _args = JSON.stringify(args);
    }

    var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });
    return syncPost('/plugins/run', {name:'mysql', func:method, args:_args});
}

function runInfo(){
    myPost('run_info','',function(data){

        var rdata = $.parseJSON(data.data);
        if (typeof(rdata['status']) != 'undefined'){
            layer.msg(rdata['msg'],{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }

        var cache_size = ((parseInt(rdata.Qcache_hits) / (parseInt(rdata.Qcache_hits) + parseInt(rdata.Qcache_inserts))) * 100).toFixed(2) + '%';
        if (cache_size == 'NaN%') cache_size = 'OFF';
        var Con = '<div class="divtable"><table class="table table-hover table-bordered" style="margin-bottom:10px;background-color:#fafafa">\
                    <tbody>\
                        <tr><th>Start Time</th><td>' + getLocalTime(rdata.Run) + '</td><th>Queries per second</th><td>' + parseInt(rdata.Questions / rdata.Uptime) + '</td></tr>\
                        <tr><th>Total connections</th><td>' + rdata.Connections + '</td><th>Transactions per second</th><td>' + parseInt((parseInt(rdata.Com_commit) + parseInt(rdata.Com_rollback)) / rdata.Uptime) + '</td></tr>\
                        <tr><th>Send</th><td>' + toSize(rdata.Bytes_sent) + '</td><th>File</th><td>' + rdata.File + '</td></tr>\
                        <tr><th>Take over</th><td>' + toSize(rdata.Bytes_received) + '</td><th>Position</th><td>' + rdata.Position + '</td></tr>\
                    </tbody>\
                    </table>\
                    <table class="table table-hover table-bordered">\
                    <thead style="display:none;"><th></th><th></th><th></th><th></th></thead>\
                    <tbody>\
                        <tr><th>Active/Peak Connections</th><td>' + rdata.Threads_running + '/' + rdata.Max_used_connections + '</td><td colspan="2">If the value is too large, increase max_connections</td></tr>\
                        <tr><th>Thread cache hit rate</th><td>' + ((1 - rdata.Threads_created / rdata.Connections) * 100).toFixed(2) + '%</td><td colspan="2">If it is too low, increase thread_cache_size</td></tr>\
                        <tr><th>Index hit rate</th><td>' + ((1 - rdata.Key_reads / rdata.Key_read_requests) * 100).toFixed(2) + '%</td><td colspan="2">If it is too low, increase key_buffer_size</td></tr>\
                        <tr><th>Innodb index hit rate</th><td>' + ((1 - rdata.Innodb_buffer_pool_reads / rdata.Innodb_buffer_pool_read_requests) * 100).toFixed(2) + '%</td><td colspan="2">If it is too low, increase innodb_buffer_pool_size</td></tr>\
                        <tr><th>Query cache hit rate</th><td>' + cache_size + '</td><td colspan="2">' + lan.soft.mysql_status_ps5 + '</td></tr>\
                        <tr><th>Create temporary table to disk</th><td>' + ((rdata.Created_tmp_disk_tables / rdata.Created_tmp_tables) * 100).toFixed(2) + '%</td><td colspan="2">If too large, try to increase tmp_table_size</td></tr>\
                        <tr><th>Opened table</th><td>' + rdata.Open_tables + '</td><td colspan="2">If too large, increase table_cache_size</td></tr>\
                        <tr><th>Amount of unused index</th><td>' + rdata.Select_full_join + '</td><td colspan="2">If it is not 0, please check whether the index of the data table is reasonable</td></tr>\
                        <tr><th>Amount of JOINs without indexes</th><td>' + rdata.Select_range_check + '</td><td colspan="2">If it is not 0, please check whether the index of the data table is reasonable</td></tr>\
                        <tr><th>number of merges after sorting</th><td>' + rdata.Sort_merge_passes + '</td><td colspan="2">If the value is too large, increase sort_buffer_size</td></tr>\
                        <tr><th>Number of table locks</th><td>' + rdata.Table_locks_waited + '</td><td colspan="2">If the value is too large, please consider increasing your database performance</td></tr>\
                    <tbody>\
            </table></div>';
        $(".soft-man-con").html(Con);
    });
}


function myDbPos(){
    myPost('my_db_pos','',function(data){
        var con = '<div class="line ">\
            <div class="info-r  ml0">\
            <input id="datadir" name="datadir" class="bt-input-text mr5 port" type="text" style="width:330px" value="'+data.data+'">\
            <span class="glyphicon cursor mr5 glyphicon-folder-open icon_datadir" onclick="changePath(\'datadir\')"></span>\
            <button id="btn_change_path" name="btn_change_path" class="btn btn-success btn-sm mr5 ml5 btn_change_port">Move</button>\
            </div></div>';
        $(".soft-man-con").html(con);

        $('#btn_change_path').click(function(){
            var datadir = $("input[name='datadir']").val();
            myPost('set_db_pos','datadir='+datadir,function(data){
                var rdata = $.parseJSON(data.data);
                layer.msg(rdata.msg,{icon:rdata.status ? 1 : 5,time:2000,shade: [0.3, '#000']});
            });
        });
    });
}

function myPort(){
    myPost('my_port','',function(data){
        var con = '<div class="line ">\
            <div class="info-r  ml0">\
            <input name="port" class="bt-input-text mr5 port" type="text" style="width:100px" value="'+data.data+'">\
            <button id="btn_change_port" name="btn_change_port" class="btn btn-success btn-sm mr5 ml5 btn_change_port">Modify</button>\
            </div></div>';
        $(".soft-man-con").html(con);

        $('#btn_change_port').click(function(){
            var port = $("input[name='port']").val();
            myPost('set_my_port','port='+port,function(data){
                var rdata = $.parseJSON(data.data);
                if (rdata.status){
                    layer.msg('Successfully modified!',{icon:1,time:2000,shade: [0.3, '#000']});
                } else {
                    layer.msg(rdata.msg,{icon:1,time:2000,shade: [0.3, '#000']});
                }
            });
        });
    });
}


function changeMySQLDataPath(act) {
    if (act != undefined) {
        layer.confirm(lan.soft.mysql_to_msg, { closeBtn: 2, icon: 3 }, function() {
            var datadir = $("#datadir").val();
            var data = 'datadir=' + datadir;
            var loadT = layer.msg(lan.soft.mysql_to_msg1, { icon: 16, time: 0, shade: [0.3, '#000'] });
            $.post('/database?action=SetDataDir', data, function(rdata) {
                layer.close(loadT)
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
            });
        });
        return;
    }

    $.post('/database?action=GetMySQLInfo', '', function(rdata) {
        var LimitCon = '<p class="conf_p">\
                            <input id="datadir" class="phpUploadLimit bt-input-text mr5" style="width:350px;" type="text" value="' + rdata.datadir + '" name="datadir">\
                            <span onclick="ChangePath(\'datadir\')" class="glyphicon glyphicon-folder-open cursor mr20" style="width:auto"></span><button class="btn btn-success btn-sm" onclick="changeMySQLDataPath(1)">' + lan.soft.mysql_to + '</button>\
                        </p>';
        $(".soft-man-con").html(LimitCon);
    });
}


function myPerfOpt() {
    myPost('db_status','',function(data){
        var rdata = $.parseJSON(data.data);
        if ( typeof(rdata.status) != 'undefined' && !rdata.status){
            layer.msg(rdata.msg, {icon:2});
            return;
        }

        // console.log(rdata);
        var key_buffer_size = toSizeM(rdata.mem.key_buffer_size);
        var query_cache_size = toSizeM(rdata.mem.query_cache_size);
        var tmp_table_size = toSizeM(rdata.mem.tmp_table_size);
        var innodb_buffer_pool_size = toSizeM(rdata.mem.innodb_buffer_pool_size);
        var innodb_additional_mem_pool_size = toSizeM(rdata.mem.innodb_additional_mem_pool_size);
        var innodb_log_buffer_size = toSizeM(rdata.mem.innodb_log_buffer_size);

        var sort_buffer_size = toSizeM(rdata.mem.sort_buffer_size);
        var read_buffer_size = toSizeM(rdata.mem.read_buffer_size);
        var read_rnd_buffer_size = toSizeM(rdata.mem.read_rnd_buffer_size);
        var join_buffer_size = toSizeM(rdata.mem.join_buffer_size);
        var thread_stack = toSizeM(rdata.mem.thread_stack);
        var binlog_cache_size = toSizeM(rdata.mem.binlog_cache_size);

        var a = key_buffer_size + query_cache_size + tmp_table_size + innodb_buffer_pool_size + innodb_additional_mem_pool_size + innodb_log_buffer_size;
        var b = sort_buffer_size + read_buffer_size + read_rnd_buffer_size + join_buffer_size + thread_stack + binlog_cache_size;
        var memSize = a + rdata.mem.max_connections * b;


        var memCon = '<div class="conf_p" style="margin-bottom:0">\
                        <div style="border-bottom:#ccc 1px solid;padding-bottom:10px;margin-bottom:10px"><span><b>Maximum memory used: </b></span>\
                        <select class="bt-input-text" name="mysql_set" style="margin-left:-4px">\
                            <option value="0">Please choose</option>\
                            <option value="1">1-2GB</option>\
                            <option value="2">2-4GB</option>\
                            <option value="3">4-8GB</option>\
                            <option value="4">8-16GB</option>\
                            <option value="5">16-32GB</option>\
                        </select>\
                        <span>' + lan.soft.mysql_set_maxmem + ': </span><input style="width:70px;background-color:#eee;" class="bt-input-text mr5" name="memSize" type="text" value="' + memSize.toFixed(2) + '" readonly>MB\
                        </div>\
                        <p><span>key_buffer_size</span><input style="width: 70px;" class="bt-input-text mr5" name="key_buffer_size" value="' + key_buffer_size + '" type="number" >MB, <font>' + lan.soft.mysql_set_key_buffer_size + '</font></p>\
                        <p><span>query_cache_size</span><input style="width: 70px;" class="bt-input-text mr5" name="query_cache_size" value="' + query_cache_size + '" type="number" >MB, <font>' + lan.soft.mysql_set_query_cache_size + '</font></p>\
                        <p><span>tmp_table_size</span><input style="width: 70px;" class="bt-input-text mr5" name="tmp_table_size" value="' + tmp_table_size + '" type="number" >MB, <font>' + lan.soft.mysql_set_tmp_table_size + '</font></p>\
                        <p><span>innodb_buffer_pool_size</span><input style="width: 70px;" class="bt-input-text mr5" name="innodb_buffer_pool_size" value="' + innodb_buffer_pool_size + '" type="number" >MB, <font>' + lan.soft.mysql_set_innodb_buffer_pool_size + '</font></p>\
                        <p><span>innodb_log_buffer_size</span><input style="width: 70px;" class="bt-input-text mr5" name="innodb_log_buffer_size" value="' + innodb_log_buffer_size + '" type="number">MB, <font>' + lan.soft.mysql_set_innodb_log_buffer_size + '</font></p>\
                        <p style="display:none;"><span>innodb_additional_mem_pool_size</span><input style="width: 70px;" class="bt-input-text mr5" name="innodb_additional_mem_pool_size" value="' + innodb_additional_mem_pool_size + '" type="number" >MB</p>\
                        <p><span>sort_buffer_size</span><input style="width: 70px;" class="bt-input-text mr5" name="sort_buffer_size" value="' + (sort_buffer_size * 1024) + '" type="number" >KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_sort_buffer_size + '</font></p>\
                        <p><span>read_buffer_size</span><input style="width: 70px;" class="bt-input-text mr5" name="read_buffer_size" value="' + (read_buffer_size * 1024) + '" type="number" >KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_read_buffer_size + ' </font></p>\
                        <p><span>read_rnd_buffer_size</span><input style="width: 70px;" class="bt-input-text mr5" name="read_rnd_buffer_size" value="' + (read_rnd_buffer_size * 1024) + '" type="number" >KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_read_rnd_buffer_size + ' </font></p>\
                        <p><span>join_buffer_size</span><input style="width: 70px;" class="bt-input-text mr5" name="join_buffer_size" value="' + (join_buffer_size * 1024) + '" type="number" >KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_join_buffer_size + '</font></p>\
                        <p><span>thread_stack</span><input style="width: 70px;" class="bt-input-text mr5" name="thread_stack" value="' + (thread_stack * 1024) + '" type="number" >KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_thread_stack + '</font></p>\
                        <p><span>binlog_cache_size</span><input style="width: 70px;" class="bt-input-text mr5" name="binlog_cache_size" value="' + (binlog_cache_size * 1024) + '" type="number" >KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_binlog_cache_size + '</font></p>\
                        <p><span>thread_cache_size</span><input style="width: 70px;" class="bt-input-text mr5" name="thread_cache_size" value="' + rdata.mem.thread_cache_size + '" type="number" ><font> ' + lan.soft.mysql_set_thread_cache_size + '</font></p>\
                        <p><span>table_open_cache</span><input style="width: 70px;" class="bt-input-text mr5" name="table_open_cache" value="' + rdata.mem.table_open_cache + '" type="number" > <font>' + lan.soft.mysql_set_table_open_cache + '</font></p>\
                        <p><span>max_connections</span><input style="width: 70px;" class="bt-input-text mr5" name="max_connections" value="' + rdata.mem.max_connections + '" type="number" ><font> ' + lan.soft.mysql_set_max_connections + '</font></p>\
                        <div style="margin-top:10px; padding-right:15px" class="text-right"><button class="btn btn-success btn-sm mr5" onclick="reBootMySqld()">Restart the database</button><button class="btn btn-success btn-sm" onclick="setMySQLConf()">Save</button></div>\
                    </div>'

        $(".soft-man-con").html(memCon);

        $(".conf_p input[name*='size'],.conf_p input[name='max_connections'],.conf_p input[name='thread_stack']").change(function() {
            comMySqlMem();
        });

        $(".conf_p select[name='mysql_set']").change(function() {
            mySQLMemOpt($(this).val());
            comMySqlMem();
        });
    });
}

function reBootMySqld(){
    pluginOpService('mysql','restart','');
}


function setMySQLConf() {
    $.post('/system/system_total', '', function(memInfo) {
        var memSize = memInfo['memTotal'];
        var setSize = parseInt($("input[name='memSize']").val());

        if(memSize < setSize){
            var errMsg = "Error, memory allocation is too high!<p style='color:red;'>Physical memory: {1}MB<br>Maximum used memory: {2}MB<br>Possible consequences: cause database instability, even Unable to start MySQLd service!";
            var msg = errMsg.replace('{1}',memSize).replace('{2}',setSize);
            layer.msg(msg,{icon:2,time:5000});
            return;
        }

        var query_cache_size = parseInt($("input[name='query_cache_size']").val());
        var query_cache_type = 0;
        if (query_cache_size > 0) {
            query_cache_type = 1;
        }
        var data = {
            key_buffer_size: parseInt($("input[name='key_buffer_size']").val()),
            query_cache_size: query_cache_size,
            query_cache_type: query_cache_type,
            tmp_table_size: parseInt($("input[name='tmp_table_size']").val()),
            max_heap_table_size: parseInt($("input[name='tmp_table_size']").val()),
            innodb_buffer_pool_size: parseInt($("input[name='innodb_buffer_pool_size']").val()),
            innodb_log_buffer_size: parseInt($("input[name='innodb_log_buffer_size']").val()),
            sort_buffer_size: parseInt($("input[name='sort_buffer_size']").val()),
            read_buffer_size: parseInt($("input[name='read_buffer_size']").val()),
            read_rnd_buffer_size: parseInt($("input[name='read_rnd_buffer_size']").val()),
            join_buffer_size: parseInt($("input[name='join_buffer_size']").val()),
            thread_stack: parseInt($("input[name='thread_stack']").val()),
            binlog_cache_size: parseInt($("input[name='binlog_cache_size']").val()),
            thread_cache_size: parseInt($("input[name='thread_cache_size']").val()),
            table_open_cache: parseInt($("input[name='table_open_cache']").val()),
            max_connections: parseInt($("input[name='max_connections']").val())
        };

        myPost('set_db_status', data, function(data){
            var rdata = $.parseJSON(data.data);
            showMsg(rdata.msg,function(){
                reBootMySqld();
            },{ icon: rdata.status ? 1 : 2 });
        });
    },'json');
}


function mySQLMemOpt(opt) {
    var query_size = parseInt($("input[name='query_cache_size']").val());
    switch (opt) {
        case '0':
            $("input[name='key_buffer_size']").val(8);
            if (query_size) $("input[name='query_cache_size']").val(4);
            $("input[name='tmp_table_size']").val(8);
            $("input[name='innodb_buffer_pool_size']").val(16);
            $("input[name='sort_buffer_size']").val(256);
            $("input[name='read_buffer_size']").val(256);
            $("input[name='read_rnd_buffer_size']").val(128);
            $("input[name='join_buffer_size']").val(128);
            $("input[name='thread_stack']").val(256);
            $("input[name='binlog_cache_size']").val(32);
            $("input[name='thread_cache_size']").val(4);
            $("input[name='table_open_cache']").val(32);
            $("input[name='max_connections']").val(500);
            break;
        case '1':
            $("input[name='key_buffer_size']").val(128);
            if (query_size) $("input[name='query_cache_size']").val(64);
            $("input[name='tmp_table_size']").val(64);
            $("input[name='innodb_buffer_pool_size']").val(256);
            $("input[name='sort_buffer_size']").val(768);
            $("input[name='read_buffer_size']").val(768);
            $("input[name='read_rnd_buffer_size']").val(512);
            $("input[name='join_buffer_size']").val(1024);
            $("input[name='thread_stack']").val(256);
            $("input[name='binlog_cache_size']").val(64);
            $("input[name='thread_cache_size']").val(64);
            $("input[name='table_open_cache']").val(128);
            $("input[name='max_connections']").val(100);
            break;
        case '2':
            $("input[name='key_buffer_size']").val(256);
            if (query_size) $("input[name='query_cache_size']").val(128);
            $("input[name='tmp_table_size']").val(384);
            $("input[name='innodb_buffer_pool_size']").val(384);
            $("input[name='sort_buffer_size']").val(768);
            $("input[name='read_buffer_size']").val(768);
            $("input[name='read_rnd_buffer_size']").val(512);
            $("input[name='join_buffer_size']").val(2048);
            $("input[name='thread_stack']").val(256);
            $("input[name='binlog_cache_size']").val(64);
            $("input[name='thread_cache_size']").val(96);
            $("input[name='table_open_cache']").val(192);
            $("input[name='max_connections']").val(200);
            break;
        case '3':
            $("input[name='key_buffer_size']").val(384);
            if (query_size) $("input[name='query_cache_size']").val(192);
            $("input[name='tmp_table_size']").val(512);
            $("input[name='innodb_buffer_pool_size']").val(512);
            $("input[name='sort_buffer_size']").val(1024);
            $("input[name='read_buffer_size']").val(1024);
            $("input[name='read_rnd_buffer_size']").val(768);
            $("input[name='join_buffer_size']").val(2048);
            $("input[name='thread_stack']").val(256);
            $("input[name='binlog_cache_size']").val(128);
            $("input[name='thread_cache_size']").val(128);
            $("input[name='table_open_cache']").val(384);
            $("input[name='max_connections']").val(300);
            break;
        case '4':
            $("input[name='key_buffer_size']").val(512);
            if (query_size) $("input[name='query_cache_size']").val(256);
            $("input[name='tmp_table_size']").val(1024);
            $("input[name='innodb_buffer_pool_size']").val(1024);
            $("input[name='sort_buffer_size']").val(2048);
            $("input[name='read_buffer_size']").val(2048);
            $("input[name='read_rnd_buffer_size']").val(1024);
            $("input[name='join_buffer_size']").val(4096);
            $("input[name='thread_stack']").val(384);
            $("input[name='binlog_cache_size']").val(192);
            $("input[name='thread_cache_size']").val(192);
            $("input[name='table_open_cache']").val(1024);
            $("input[name='max_connections']").val(400);
            break;
        case '5':
            $("input[name='key_buffer_size']").val(1024);
            if (query_size) $("input[name='query_cache_size']").val(384);
            $("input[name='tmp_table_size']").val(2048);
            $("input[name='innodb_buffer_pool_size']").val(4096);
            $("input[name='sort_buffer_size']").val(4096);
            $("input[name='read_buffer_size']").val(4096);
            $("input[name='read_rnd_buffer_size']").val(2048);
            $("input[name='join_buffer_size']").val(8192);
            $("input[name='thread_stack']").val(512);
            $("input[name='binlog_cache_size']").val(256);
            $("input[name='thread_cache_size']").val(256);
            $("input[name='table_open_cache']").val(2048);
            $("input[name='max_connections']").val(500);
            break;
    }
}

function comMySqlMem() {
    var key_buffer_size = parseInt($("input[name='key_buffer_size']").val());
    var query_cache_size = parseInt($("input[name='query_cache_size']").val());
    var tmp_table_size = parseInt($("input[name='tmp_table_size']").val());
    var innodb_buffer_pool_size = parseInt($("input[name='innodb_buffer_pool_size']").val());
    var innodb_additional_mem_pool_size = parseInt($("input[name='innodb_additional_mem_pool_size']").val());
    var innodb_log_buffer_size = parseInt($("input[name='innodb_log_buffer_size']").val());

    var sort_buffer_size = $("input[name='sort_buffer_size']").val() / 1024;
    var read_buffer_size = $("input[name='read_buffer_size']").val() / 1024;
    var read_rnd_buffer_size = $("input[name='read_rnd_buffer_size']").val() / 1024;
    var join_buffer_size = $("input[name='join_buffer_size']").val() / 1024;
    var thread_stack = $("input[name='thread_stack']").val() / 1024;
    var binlog_cache_size = $("input[name='binlog_cache_size']").val() / 1024;
    var max_connections = $("input[name='max_connections']").val();

    var a = key_buffer_size + query_cache_size + tmp_table_size + innodb_buffer_pool_size + innodb_additional_mem_pool_size + innodb_log_buffer_size
    var b = sort_buffer_size + read_buffer_size + read_rnd_buffer_size + join_buffer_size + thread_stack + binlog_cache_size
    var memSize = a + max_connections * b
    $("input[name='memSize']").val(memSize.toFixed(2));
}

function syncGetDatabase(){
    myPost('sync_get_databases', null, function(data){
        var rdata = $.parseJSON(data.data);
        showMsg(rdata.msg,function(){
            dbList();
        },{ icon: rdata.status ? 1 : 2 });
    });
}

function syncToDatabase(type){
    var data = [];
    $('input[type="checkbox"].check:checked').each(function () {
        if (!isNaN($(this).val())) data.push($(this).val());
    });
    var postData = 'type='+type+'&ids='+JSON.stringify(data);
    myPost('sync_to_databases', postData, function(data){
        var rdata = $.parseJSON(data.data);
        // console.log(rdata);
        showMsg(rdata.msg,function(){
            dbList();
        },{ icon: rdata.status ? 1 : 2 });
    });
}

function setRootPwd(type, pwd){
    if (type==1){
        var password = $("#MyPassword").val();
        myPost('set_root_pwd', {password:password}, function(data){
            var rdata = $.parseJSON(data.data);
            showMsg(rdata.msg,function(){
                dbList();
                $('.layui-layer-close1').click();
            },{icon: rdata.status ? 1 : 2});
        });
        return;
    }

    var index = layer.open({
        type: 1,
        area: '500px',
        title: 'Change database password',
        closeBtn: 1,
        shift: 5,
        btn:["Submit","Cancel"],
        shadeClose: true,
        content: "<form class='bt-form pd20' id='mod_pwd'>\
                    <div class='line'>\
                        <span class='tname'>root password</span>\
                        <div class='info-r'><input class='bt-input-text mr5' type='text' name='password' id='MyPassword' style='width:330px' value='"+pwd+"' />\
                            <span title='random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span>\
                        </div>\
                    </div>\
                  </form>",
        yes:function(){
            setRootPwd(1);
        }
    });
}

function showHidePass(obj){
    var a = "glyphicon-eye-open";
    var b = "glyphicon-eye-close";

    if($(obj).hasClass(a)){
        $(obj).removeClass(a).addClass(b);
        $(obj).prev().text($(obj).prev().attr('data-pw'))
    }
    else{
        $(obj).removeClass(b).addClass(a);
        $(obj).prev().text('***');
    }
}

function checkSelect(){
    setTimeout(function () {
        var num = $('input[type="checkbox"].check:checked').length;
        // console.log(num);
        if (num == 1) {
            $('button[batch="true"]').hide();
            $('button[batch="false"]').show();
        }else if (num>1){
            $('button[batch="true"]').show();
            $('button[batch="false"]').show();
        }else{
            $('button[batch="true"]').hide();
            $('button[batch="false"]').hide();
        }
    },5)
}

function setDbRw(id,username,val){
    myPost('get_db_rw',{id:id,username:username,rw:val}, function(data){
        var rdata = $.parseJSON(data.data);
        // layer.msg(rdata.msg,{icon:rdata.status ? 1 : 5,shade: [0.3, '#000']});
        showMsg(rdata.msg, function(){
            dbList();
        },{icon:rdata.status ? 1 : 5,shade: [0.3, '#000']}, 2000);

    });
}

function setDbAccess(username){
    myPost('get_db_access','username='+username, function(data){
        var rdata = $.parseJSON(data.data);
        if (!rdata.status){
            layer.msg(rdata.msg,{icon:2,shade: [0.3, '#000']});
            return;
        }

        var index = layer.open({
            type: 1,
            area: '500px',
            title: 'Set database permissions',
            closeBtn: 1,
            shift: 5,
            btn:["Submit","Cancel"],
            shadeClose: true,
            content: "<form class='bt-form pd20' id='set_db_access'>\
                        <div class='line'>\
                            <span class='tname'>Access permission</span>\
                            <div class='info-r '>\
                                <select class='bt-input-text mr5' name='dataAccess' style='width:100px'>\
                                <option value='127.0.0.1'>Localhost</option>\
                                <option value=\"%\">Everyone</option>\
                                <option value='ip'>Spesific IP</option>\
                                </select>\
                            </div>\
                        </div>\
                      </form>",
            success:function(){
                if (rdata.msg == '127.0.0.1'){
                    $('select[name="dataAccess"]').find("option[value='127.0.0.1']").attr("selected",true);
                } else if (rdata.msg == '%'){
                    $('select[name="dataAccess"]').find('option[value="%"]').attr("selected",true);
                } else if ( rdata.msg == 'ip' ){
                    $('select[name="dataAccess"]').find('option[value="ip"]').attr("selected",true);
                    $('select[name="dataAccess"]').after("<input id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                } else {
                    $('select[name="dataAccess"]').find('option[value="ip"]').attr("selected",true);
                    $('select[name="dataAccess"]').after("<input value='"+rdata.msg+"' id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                }

                 $('select[name="dataAccess"]').change(function(){
                    var v = $(this).val();
                    if (v == 'ip'){
                        $(this).after("<input id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                    } else {
                        $('#dataAccess_subid').remove();
                    }
                });
            },
            yes:function(index){
                var data = $("#set_db_access").serialize();
                data = decodeURIComponent(data);
                var dataObj = toArrayObject(data);
                if(!dataObj['access']){
                    dataObj['access'] = dataObj['dataAccess'];
                    if ( dataObj['dataAccess'] == 'ip'){
                        if (dataObj['address']==''){
                            layer.msg('IP address cannot be empty!',{icon:2,shade: [0.3, '#000']});
                            return;
                        }
                        dataObj['access'] = dataObj['address'];
                    }
                }
                dataObj['username'] = username;
                myPost('set_db_access', dataObj, function(data){
                    var rdata = $.parseJSON(data.data);
                    showMsg(rdata.msg,function(){
                        layer.close(index);
                        dbList();
                    },{icon: rdata.status ? 1 : 2});
                });
            }
        });

    });
}

function fixDbAccess(username){
    myPost('fix_db_access', '', function(rdata){
        var rdata = $.parseJSON(rdata.data);
        showMsg(rdata.msg,function(){
            dbList();
        },{icon: rdata.status ? 1 : 2});
    });
}

function setDbPass(id, username, password){

    var index = layer.open({
        type: 1,
        area: '500px',
        title: 'Change database password',
        closeBtn: 1,
        shift: 5,
        shadeClose: true,
        btn:["Submit","Cancel"],
        content: "<form class='bt-form pd20' id='mod_pwd'>\
                    <div class='line'>\
                        <span class='tname'>Username</span>\
                        <div class='info-r'><input readonly='readonly' name=\"name\" class='bt-input-text mr5' type='text' style='width:330px;outline:none;' value='"+username+"' /></div>\
                    </div>\
                    <div class='line'>\
                    <span class='tname'>Password</span>\
                    <div class='info-r'>\
                        <input class='bt-input-text mr5' type='text' name='password' id='MyPassword' style='width:330px' value='"+password+"' />\
                        <span title='Random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span></div>\
                    </div>\
                    <input type='hidden' name='id' value='"+id+"'>\
                  </form>",
        yes:function(index){
            var data = {};
            data['name'] = $('input[name=name]').val();
            data['password'] = $('#MyPassword').val();
            data['id'] = $('input[name=id]').val();
            myPost('set_user_pwd', data, function(data){
                var rdata = $.parseJSON(data.data);
                showMsg(rdata.msg,function(){
                    layer.close(index);
                    dbList();
                },{icon: rdata.status ? 1 : 2});
            });
        }
    });
}

function addDatabase(type){
    layer.open({
        type: 1,
        area: '500px',
        title: 'Add database',
        closeBtn: 1,
        shift: 5,
        shadeClose: true,
        btn:["Submit","Cancel"],
        content: "<form class='bt-form pd20' id='add_db'>\
                    <div class='line'>\
                        <span class='tname'>Database name</span>\
                        <div class='info-r'><input name='name' class='bt-input-text mr5' placeholder='New database name' type='text' style='width:65%' value=''>\
                        <select class='bt-input-text mr5 codeing_a5nGsm' name='codeing' style='width:27%'>\
                            <option value='utf8mb4'>utf8mb4</option>\
                            <option value='utf8'>utf-8</option>\
                            <option value='gbk'>gbk</option>\
                            <option value='big5'>big5</option>\
                        </select>\
                        </div>\
                    </div>\
                    <div class='line'><span class='tname'>Username</span><div class='info-r'><input name='db_user' class='bt-input-text mr5' placeholder='Database user' type='text' style='width:65%' value=''></div></div>\
                    <div class='line'>\
                    <span class='tname'>Password</span>\
                    <div class='info-r'><input class='bt-input-text mr5' type='text' name='password' id='MyPassword' style='width:330px' value='"+(randomStrPwd(16))+"' /><span title='Random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span></div>\
                    </div>\
                    <div class='line'>\
                        <span class='tname'>Access permission</span>\
                        <div class='info-r '>\
                            <select class='bt-input-text mr5' name='dataAccess' style='width:100px'>\
                            <option value='127.0.0.1'>Localhost</option>\
                            <option value=\"%\">Everyone</option>\
                            <option value='ip'>Spesific IP</option>\
                            </select>\
                        </div>\
                    </div>\
                    <input type='hidden' name='ps' value='' />\
                  </form>",
        success:function(){
            $("input[name='name']").keyup(function(){
                var v = $(this).val();
                $("input[name='db_user']").val(v);
                $("input[name='ps']").val(v);
            });

            $('select[name="dataAccess"]').change(function(){
                var v = $(this).val();
                if (v == 'ip'){
                    $(this).after("<input id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                } else {
                    $('#dataAccess_subid').remove();
                }
            });
        },
        yes:function(index) {
            var data = $("#add_db").serialize();
            data = decodeURIComponent(data);
            var dataObj = toArrayObject(data);
            if(!dataObj['address']){
                dataObj['address'] = dataObj['dataAccess'];
            }
            myPost('add_db', dataObj, function(data){
                var rdata = $.parseJSON(data.data);
                showMsg(rdata.msg,function(){
                    if (rdata.status){
                        layer.close(index);
                        dbList();
                    }
                },{icon: rdata.status ? 1 : 2},600);
            });
        }
    });
}

function delDb(id, name){
    safeMessage('Delete ['+name+']', 'Do you really want to delete ['+name+']？',function(){
        var data='id='+id+'&name='+name
        myPost('del_db', data, function(data){
            var rdata = $.parseJSON(data.data);
            showMsg(rdata.msg,function(){
                dbList();
            },{icon: rdata.status ? 1 : 2}, 600);
        });
    });
}

function delDbBatch(){
    var arr = [];
    $('input[type="checkbox"].check:checked').each(function () {
        var _val = $(this).val();
        var _name = $(this).parent().next().text();
        if (!isNaN(_val)) {
            arr.push({'id':_val,'name':_name});
        }
    });

    safeMessage('Delete databases in batches','<a style="color:red;">You have selected [2] databases in total, and they cannot be restored after deletion. Do you really want to delete them?</a>',function(){
        var i = 0;
        $(arr).each(function(){
            var data  = myAsyncPost('del_db', this);
            var rdata = $.parseJSON(data.data);
            if (!rdata.status){
                layer.msg(rdata.msg,{icon:2,time:2000,shade: [0.3, '#000']});
            }
            i++;
        });

        var msg = 'Successfully deleted ['+i+'] databases!';
        showMsg(msg,function(){
            dbList();
        },{icon: 1}, 600);
    });
}


function setDbPs(id, name, obj) {
    var _span = $(obj);
    var _input = $("<input class='baktext' value=\""+_span.text()+"\" type='text' placeholder='Descriptions' />");
    _span.hide().after(_input);
    _input.focus();
    _input.blur(function(){
        $(this).remove();
        var ps = _input.val();
        _span.text(ps).show();
        var data = {name:name,id:id,ps:ps};
        myPost('set_db_ps', data, function(data){
            var rdata = $.parseJSON(data.data);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        });
    });
    _input.keyup(function(){
        if(event.keyCode == 13){
            _input.trigger('blur');
        }
    });
}

function openPhpmyadmin(name,username,password){

    data = syncPost('/plugins/check',{'name':'phpmyadmin'});


    if (!data.status){
        layer.msg(data.msg,{icon:2,shade: [0.3, '#000']});
        return;
    }

    data = syncPost('/plugins/run',{'name':'phpmyadmin','func':'status'});
    if (data.data != 'start'){
        layer.msg('phpMyAdmin not started',{icon:2,shade: [0.3, '#000']});
        return;
    }

    data = syncPost('/plugins/run',{'name':'phpmyadmin','func':'get_cfg'});
    var rdata = $.parseJSON(data.data);
    if (rdata.choose != 'mariadb'){
        layer.msg('Currently it is ['+rdata.choose+'] mode, if you want to use it, please modify the phpMyAdmin access switch.',{icon:2,shade: [0.3, '#000']});
        return;
    }
    var phpmyadmin_cfg = rdata;

    data = syncPost('/plugins/run',{'name':'phpmyadmin','func':'get_home_page'});
    var rdata = $.parseJSON(data.data);
    if (!rdata.status){
        layer.msg(rdata.msg,{icon:2,shade: [0.3, '#000']});
        return;
    }

    var home_page = rdata.data;
    home_page = home_page.replace("http://","http://"+phpmyadmin_cfg['username']+":"+phpmyadmin_cfg['password']+"@");
    $("#toPHPMyAdmin").attr('action',home_page);

    if($("#toPHPMyAdmin").attr('action').indexOf('phpmyadmin') == -1){
        layer.msg('Please install phpMyAdmin first',{icon:2,shade: [0.3, '#000']});
        setTimeout(function(){ window.location.href = '/soft'; },3000);
        return;
    }

    data = syncPost('/plugins/run',{'name':'phpmyadmin','func':'version'});
    bigVer = data.data.split('.')[0]
    if (bigVer>=4.5){

        setTimeout(function(){
            $("#toPHPMyAdmin").submit();
        },3000);
        layer.msg('phpMyAdmin['+data.data+'] requires manual login 😭',{icon:16,shade: [0.3, '#000'],time:4000});

    } else{
        var murl = $("#toPHPMyAdmin").attr('action');
        $("#pma_username").val(username);
        $("#pma_password").val(password);
        $("#db").val(name);

        layer.msg('Opening phpMyAdmin',{icon:16,shade: [0.3, '#000'],time:2000});

        setTimeout(function(){
            $("#toPHPMyAdmin").submit();
        },3000);
    }
}

function delBackup(filename, name, path){
    if(typeof(path) == "undefined"){
        path = "";
    }
    myPost('delete_db_backup',{filename:filename,path:path},function(){
        layer.msg('Execution succeed!');
        setTimeout(function(){
            setBackupReq(name);
        },2000);
    });
}

function downloadBackup(file){
    window.open('/files/download?filename='+encodeURIComponent(file));
}

function importBackup(file,name){
    myPost('import_db_backup',{file:file,name:name}, function(data){
        // console.log(data);
        layer.msg('Execution succeed!');
    });
}


function importDbExternal(file,name){
    myPost('import_db_external',{file:file,name:name}, function(data){
        layer.msg('Execution succeed!');
    });
}

function setLocalImport(db_name){

    function uploadDbFiles(upload_dir){
        var up_db = layer.open({
            type:1,
            closeBtn: 1,
            title:"Upload import file ["+upload_dir+']',
            area: ['500px','300px'],
            shadeClose:false,
            content:'<div class="fileUploadDiv">\
                    <input type="hidden" id="input-val" value="'+upload_dir+'" />\
                    <input type="file" id="file_input"  multiple="true" autocomplete="off" />\
                    <button type="button"  id="opt" autocomplete="off">Add files</button>\
                    <button type="button" id="up" autocomplete="off" >Start upload</button>\
                    <span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
                    <span style="float:right;margin-top: 9px;">\
                    <font>File encoding:</font>\
                    <select id="fileCodeing" >\
                        <option value="byte">binary</option>\
                        <option value="utf-8">UTF-8</option>\
                        <option value="gb18030">GB2312</option>\
                    </select>\
                    </span>\
                    <button type="button" id="filesClose" autocomplete="off">Cancel</button>\
                    <ul id="up_box"></ul>\
                </div>',
            success:function(){
                $('#filesClose').click(function(){
                    layer.close(up_db);
                });
            }

        });
        uploadStart(function(){
            getList();
            layer.close(up_db);
        });
    }

    function getList(){
        myPost('get_db_backup_import_list',{}, function(data){
            var rdata = $.parseJSON(data.data);

            var file_list = rdata.data.list;
            var upload_dir = rdata.data.upload_dir;

            var tbody = '';
            for (var i = 0; i < file_list.length; i++) {
                tbody += '<tr>\
                        <td><span> ' + file_list[i]['name'] + '</span></td>\
                        <td><span> ' + file_list[i]['size'] + '</span></td>\
                        <td><span> ' + file_list[i]['time'] + '</span></td>\
                        <td style="text-align: right;">\
                            <a class="btlink" onclick="importDbExternal(\'' + file_list[i]['name'] + '\',\'' +db_name+ '\')">Import</a> | \
                            <a class="btlink del" index="'+i+'">Delete</a>\
                        </td>\
                    </tr>';
            }

            $('#import_db_file_list').html(tbody);
            $('input[name="upload_dir"]').val(upload_dir);

            $("#import_db_file_list .del").on('click',function(){
                var index = $(this).attr('index');
                var filename = file_list[index]["name"];
                myPost('delete_db_backup',{filename:filename,path:upload_dir},function(){
                    showMsg('Execution succeed!', function(){
                        getList();
                    },{icon:1},2000);
                });
            });
        });
    }

    var layerIndex = layer.open({
        type: 1,
        title: "Import data from file",
        area: ['600px', '380px'],
        closeBtn: 1,
        shadeClose: false,
        content: '<div class="pd15">\
                    <div class="db_list">\
                        <button id="btn_file_upload" class="btn btn-success btn-sm" type="button">Upload from local</button>\
                    </div >\
                    <div class="divtable">\
                    <input type="hidden" name="upload_dir" value=""> \
                    <div id="database_fix"  style="height:150px;overflow:auto;border:#ddd 1px solid">\
                    <table class="table table-hover "style="border:none">\
                        <thead>\
                            <tr>\
                                <th>File name</th>\
                                <th>File size</th>\
                                <th>Backup time</th>\
                                <th style="text-align: right;">Action</th>\
                            </tr>\
                        </thead>\
                        <tbody  id="import_db_file_list" class="gztr"></tbody>\
                    </table>\
                    </div>\
                    <ul class="help-info-text c7">\
                        <li>Only sql, zip, sql.gz, (tar.gz|gz|tgz) are supported</li>\
                        <li>Zip, tar.gz compressed package structure: test.zip or test.tar.gz compressed package must contain test.sql</li>\
                        <li>If the file is too large, you can also use the SFTP tool to upload the database file to /home/slemp/backup/import</li>\
                    </ul>\
                </div>\
        </div>',
        success:function(index){
            $('#btn_file_upload').click(function(){
                var upload_dir = $('input[name="upload_dir"]').val();
                uploadDbFiles(upload_dir);
            });
            getList();
        },
    });
}


function setBackup(db_name){
    var layerIndex = layer.open({
        type: 1,
        title: "Database Backup Details",
        area: ['600px', '280px'],
        closeBtn: 1,
        shadeClose: false,
        content: '<div class="pd15">\
                    <div class="db_list">\
                        <button id="btn_backup" class="btn btn-success btn-sm" type="button">Backup</button>\
                        <button id="btn_local_import" class="btn btn-success btn-sm" type="button">External import</button>\
                    </div >\
                    <div class="divtable">\
                    <div  id="database_fix"  style="height:150px;overflow:auto;border:#ddd 1px solid">\
                    <table id="database_table" class="table table-hover "style="border:none">\
                        <thead>\
                            <tr>\
                                <th>Filename</th>\
                                <th>Size</th>\
                                <th>Backup time</th>\
                                <th style="text-align: right;">Action</th>\
                            </tr>\
                        </thead>\
                        <tbody class="list"></tbody>\
                    </table>\
                    </div>\
                </div>\
        </div>',
        success:function(index){
            $('#btn_backup').click(function(){
                myPost('set_db_backup',{name:db_name}, function(data){
                    showMsg('Execution succeed!', function(){
                        setBackupReq(db_name);
                    }, {icon:1}, 2000);
                });
            });

            $('#btn_local_import').click(function(){
                setLocalImport(db_name);
            });

            setBackupReq(db_name);
        },
    });
}


function setBackupReq(db_name, obj){
     myPost('get_db_backup_list', {name:db_name}, function(data){
        var rdata = $.parseJSON(data.data);
        var tbody = '';
        for (var i = 0; i < rdata.data.length; i++) {
            tbody += '<tr>\
                    <td><span> ' + rdata.data[i]['name'] + '</span></td>\
                    <td><span> ' + rdata.data[i]['size'] + '</span></td>\
                    <td><span> ' + rdata.data[i]['time'] + '</span></td>\
                    <td style="text-align: right;">\
                        <a class="btlink" onclick="importBackup(\'' + rdata.data[i]['name'] + '\',\'' +db_name+ '\')">Import</a> | \
                        <a class="btlink" onclick="downloadBackup(\'' + rdata.data[i]['file'] + '\')">Download</a> | \
                        <a class="btlink" onclick="delBackup(\'' + rdata.data[i]['name'] + '\',\'' +db_name+ '\')">Delete</a>\
                    </td>\
                </tr> ';
        }
        $('#database_table tbody').html(tbody);
    });
}


function dbList(page, search){
    var _data = {};
    if (typeof(page) =='undefined'){
        var page = 1;
    }

    _data['page'] = page;
    _data['page_size'] = 10;
    if(typeof(search) != 'undefined'){
        _data['search'] = search;
    }
    myPost('get_db_list', _data, function(data){
        var rdata = $.parseJSON(data.data);
        var list = '';
        for(i in rdata.data){
            list += '<tr>';
            list +='<td><input value="'+rdata.data[i]['id']+'" class="check" onclick="checkSelect();" type="checkbox"></td>';
            list += '<td>' + rdata.data[i]['name'] +'</td>';
            list += '<td>' + rdata.data[i]['username'] +'</td>';
            list += '<td>' +
                        '<span class="password" data-pw="'+rdata.data[i]['password']+'">***</span>' +
                        '<span onclick="showHidePass(this)" class="glyphicon glyphicon-eye-open cursor pw-ico" style="margin-left:10px"></span>'+
                        '<span class="ico-copy cursor btcopy" style="margin-left:10px" title="Copy password" onclick="copyPass(\''+rdata.data[i]['password']+'\')"></span>'+
                    '</td>';


            list += '<td><span class="c9 input-edit" onclick="setDbPs(\''+rdata.data[i]['id']+'\',\''+rdata.data[i]['name']+'\',this)" style="display: inline-block;">'+rdata.data[i]['ps']+'</span></td>';
            list += '<td style="text-align:right">';

            list += '<a href="javascript:;" class="btlink" class="btlink" onclick="setBackup(\''+rdata.data[i]['name']+'\')" title="Database backup">'+(rdata.data[i]['is_backup']?'Backup':'No Backup') +'</a> | ';

            var rw = '';
            var rw_change = 'all';
            if (typeof(rdata.data[i]['rw'])!='undefined'){
                var rw_val = 'Read and Write';
                if (rdata.data[i]['rw'] == 'all'){
                    rw_val = "All";
                    rw_change = 'rw';
                } else if (rdata.data[i]['rw'] == 'rw'){
                    rw_val = "Read and Write";
                    rw_change = 'r';
                } else if (rdata.data[i]['rw'] == 'r'){
                    rw_val = "Read only";
                    rw_change = 'all';
                }
                rw = '<a href="javascript:;" class="btlink" onclick="setDbRw(\''+rdata.data[i]['id']+'\',\''+rdata.data[i]['name']+'\',\''+rw_change+'\')" title="Set read and write">'+rw_val+'</a> | ';
            }


            list += '<a href="javascript:;" class="btlink" onclick="openPhpmyadmin(\''+rdata.data[i]['name']+'\',\''+rdata.data[i]['username']+'\',\''+rdata.data[i]['password']+'\')" title="Database management">Manage</a> | ' +
                        '<a href="javascript:;" class="btlink" onclick="repTools(\''+rdata.data[i]['name']+'\')" title="MySQL optimization repair tool">Tool</a> | ' +
                        '<a href="javascript:;" class="btlink" onclick="setDbAccess(\''+rdata.data[i]['username']+'\')" title="Set database permissions">Permissions</a> | ' +
                        rw +
                        '<a href="javascript:;" class="btlink" onclick="setDbPass('+rdata.data[i]['id']+',\''+ rdata.data[i]['username'] +'\',\'' + rdata.data[i]['password'] + '\')">Change encryption</a> | ' +
                        '<a href="javascript:;" class="btlink" onclick="delDb(\''+rdata.data[i]['id']+'\',\''+rdata.data[i]['name']+'\')" title="Delete database">Delete</a>' +
                    '</td>';
            list += '</tr>';
        }

        var con = '<div class="safe bgw">\
            <button onclick="addDatabase()" title="Add database" class="btn btn-success btn-sm" type="button" style="margin-right: 5px;">Add database</button>\
            <button onclick="setRootPwd(0,\''+rdata.info['root_pwd']+'\')" title="Set MySQL administrator password" class="btn btn-default btn-sm" type="button" style="margin-right: 5px;">Root password</button>\
            <button onclick="openPhpmyadmin(\'\',\'root\',\''+rdata.info['root_pwd']+'\')" title="Open phpMyadmin" class="btn btn-default btn-sm" type="button" style="margin-right: 5px;">phpMyAdmin</button>\
            <button onclick="setDbAccess(\'root\')" title="ROOT permission" class="btn btn-default btn-sm" type="button" style="margin-right: 5px;">ROOT permission</button>\
            <button onclick="fixDbAccess(\'root\')" title="Repair" class="btn btn-default btn-sm" type="button" style="margin-right: 5px;">Repair</button>\
            <span style="float:right">              \
                <button batch="true" style="float: right;display: none;margin-left:10px;" onclick="delDbBatch();" title="Delete selected" class="btn btn-default btn-sm">Delete selected</button>\
            </span>\
            <div class="divtable mtb10">\
                <div class="tablescroll">\
                    <table id="DataBody" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0" style="border: 0 none;">\
                    <thead><tr><th width="30"><input class="check" onclick="checkSelect();" type="checkbox"></th>\
                    <th>Database name</th>\
                    <th>Username</th>\
                    <th>Password</th>\
                    '+
                    // '<th>Backup</th>'+
                    '<th>Descriptions</th>\
                    <th style="text-align:right;">Action</th></tr></thead>\
                    <tbody>\
                    '+ list +'\
                    </tbody></table>\
                </div>\
                <div id="databasePage" class="dataTables_paginate paging_bootstrap page"></div>\
                <div class="table_toolbar" style="left:0px;">\
                    <span class="sync btn btn-default btn-sm" style="margin-right:5px" onclick="syncToDatabase(1)" title="Synchronize the selected database information to the server">Sync selected</span>\
                    <span class="sync btn btn-default btn-sm" style="margin-right:5px" onclick="syncToDatabase(0)" title="Synchronize all database information to the server">Sync all</span>\
                    <span class="sync btn btn-default btn-sm" onclick="syncGetDatabase()" title="Get a list of databases from the server">Get from server</span>\
                </div>\
            </div>\
        </div>';

        con += '<form id="toPHPMyAdmin" action="" method="post" style="display: none;" target="_blank">\
            <input type="text" name="pma_username" id="pma_username" value="">\
            <input type="password" name="pma_password" id="pma_password" value="">\
            <input type="text" name="server" value="1">\
            <input type="text" name="target" value="index.php">\
            <input type="text" name="db" id="db" value="">\
        </form>';

        $(".soft-man-con").html(con);
        $('#databasePage').html(rdata.page);

        readerTableChecked();
    });
}


function myLogs(){

    myPost('bin_log', {status:1}, function(data){
        var rdata = $.parseJSON(data.data);

        var line_status = ""
        if (rdata.status){
            line_status = '<button class="btn btn-success btn-xs btn-bin va0">Close</button>\
                        <button class="btn btn-success btn-xs clean-btn-bin va0">Clean up BINLOG logs</button>';
        } else {
            line_status = '<button class="btn btn-success btn-xs btn-bin va0">Turn on</button>';
        }

        var limitCon = '<p class="conf_p">\
                        <span class="f14 c6 mr20">Binary log </span><span class="f14 c6 mr20">' + toSize(rdata.msg) + '</span>\
                        '+line_status+'\
                        <p class="f14 c6 mtb10" style="border-top:#ddd 1px solid; padding:10px 0">Error log<button class="btn btn-default btn-clear btn-xs" style="float:right;" >Clear log</button></p>\
                        <textarea readonly style="margin: 0px;width: 100%;height: 438px;background-color: #333;color:#fff; padding:0 5px" id="error_log"></textarea>\
                    </p>';
        $(".soft-man-con").html(limitCon);

        $(".btn-bin").click(function () {
            myPost('bin_log', 'close=change', function(data){
                var rdata = $.parseJSON(data.data);
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                setTimeout(function(){myLogs();}, 2000);
            });
        });

        $(".clean-btn-bin").click(function () {
            myPost('clean_bin_log', '', function(data){
                var rdata = $.parseJSON(data.data);
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                setTimeout(function(){myLogs();}, 2000);
            });
        });

        $(".btn-clear").click(function () {
            myPost('error_log', 'close=1', function(data){
                var rdata = $.parseJSON(data.data);
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                setTimeout(function(){myLogs();}, 2000);
            });
        })

        myPost('error_log', 'p=1', function(data){
            var rdata = $.parseJSON(data.data);
            var error_body = '';
            if (rdata.status){
                error_body = rdata.data;
            } else {
                error_body = rdata.msg;
            }
            $("#error_log").html(error_body);
            var ob = document.getElementById('error_log');
            ob.scrollTop = ob.scrollHeight;
        });
    });
}


function repCheckeds(tables) {
    var dbs = []
    if (tables) {
        dbs.push(tables)
    } else {
        var db_tools = $("input[value^='dbtools_']");
        for (var i = 0; i < db_tools.length; i++) {
            if (db_tools[i].checked) dbs.push(db_tools[i].value.replace('dbtools_', ''));
        }
    }

    if (dbs.length < 1) {
        layer.msg('Please select at least one table!', { icon: 2 });
        return false;
    }
    return dbs;
}

function repDatabase(db_name, tables) {
    dbs = repCheckeds(tables);

    myPost('repair_table', { db_name: db_name, tables: JSON.stringify(dbs) }, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        repTools(db_name, true);
    },'Repair command has been sent, please wait...');
}


function optDatabase(db_name, tables) {
    dbs = repCheckeds(tables);

    myPost('opt_table', { db_name: db_name, tables: JSON.stringify(dbs) }, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        repTools(db_name, true);
    },'Optimization command has been sent, please wait...');
}

function toDatabaseType(db_name, tables, type){
    dbs = repCheckeds(tables);
    myPost('alter_table', { db_name: db_name, tables: JSON.stringify(dbs),table_type: type }, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        repTools(db_name, true);
    }, 'Engine conversion command has been sent, please wait...');
}


function selectedTools(my_obj, db_name) {
    var is_checked = false

    if (my_obj) is_checked = my_obj.checked;
    var db_tools = $("input[value^='dbtools_']");
    var n = 0;
    for (var i = 0; i < db_tools.length; i++) {
        if (my_obj) db_tools[i].checked = is_checked;
        if (db_tools[i].checked) n++;
    }
    if (n > 0) {
        var my_btns = '<button class="btn btn-default btn-sm" onclick="repDatabase(\'' + db_name + '\',null)">Repair</button>\
            <button class="btn btn-default btn-sm" onclick="optDatabase(\'' + db_name + '\',null)">Optimization</button>\
            <button class="btn btn-default btn-sm" onclick="toDatabaseType(\'' + db_name + '\',null,\'InnoDB\')">Convert to InnoDB</button></button>\
            <button class="btn btn-default btn-sm" onclick="toDatabaseType(\'' + db_name + '\',null,\'MyISAM\')">Convert to MyISAM</button>'
        $("#db_tools").html(my_btns);
    } else {
        $("#db_tools").html('');
    }
}

function repTools(db_name, res){
    myPost('get_db_info', {name:db_name}, function(data){
        var rdata = $.parseJSON(data.data);
        var types = { InnoDB: "MyISAM", MyISAM: "InnoDB" };
        var tbody = '';
        for (var i = 0; i < rdata.tables.length; i++) {
            if (!types[rdata.tables[i].type]) continue;
            tbody += '<tr>\
                    <td><input value="dbtools_' + rdata.tables[i].table_name + '" class="check" onclick="selectedTools(null,\'' + db_name + '\');" type="checkbox"></td>\
                    <td><span style="width:220px;"> ' + rdata.tables[i].table_name + '</span></td>\
                    <td>' + rdata.tables[i].type + '</td>\
                    <td><span style="width:90px;"> ' + rdata.tables[i].collation + '</span></td>\
                    <td>' + rdata.tables[i].rows_count + '</td>\
                    <td>' + rdata.tables[i].data_size + '</td>\
                    <td style="text-align: right;">\
                        <a class="btlink" onclick="repDatabase(\''+ db_name + '\',\'' + rdata.tables[i].table_name + '\')">Repair</a> |\
                        <a class="btlink" onclick="optDatabase(\''+ db_name + '\',\'' + rdata.tables[i].table_name + '\')">Optimization</a> |\
                        <a class="btlink" onclick="toDatabaseType(\''+ db_name + '\',\'' + rdata.tables[i].table_name + '\',\'' + types[rdata.tables[i].type] + '\')"> turn into ' + types[rdata.tables[i].type] + '</a>\
                    </td>\
                </tr> '
        }

        if (res) {
            $(".gztr").html(tbody);
            $("#db_tools").html('');
            $("input[type='checkbox']").attr("checked", false);
            $(".tools_size").html('Size：' + rdata.data_size);
            return;
        }

        layer.open({
            type: 1,
            title: "MariaDB toolbox [" + db_name + "]",
            area: ['780px', '580px'],
            closeBtn: 2,
            shadeClose: false,
            content: '<div class="pd15">\
                            <div class="db_list">\
                                <span><a>Name database：'+ db_name + '</a>\
                                <a class="tools_size">Size：'+ rdata.data_size + '</a></span>\
                                <span id="db_tools" style="float: right;"></span>\
                            </div >\
                            <div class="divtable">\
                            <div  id="database_fix"  style="height:360px;overflow:auto;border:#ddd 1px solid">\
                            <table class="table table-hover "style="border:none">\
                                <thead>\
                                    <tr>\
                                        <th><input class="check" onclick="selectedTools(this,\''+ db_name + '\');" type="checkbox"></th>\
                                        <th>Table Name</th>\
                                        <th>Engine</th>\
                                        <th>Character set</th>\
                                        <th>Number of lines</th>\
                                        <th>Size</th>\
                                        <th style="text-align: right;">Action</th>\
                                    </tr>\
                                </thead>\
                                <tbody class="gztr">' + tbody + '</tbody>\
                            </table>\
                            </div>\
                        </div>\
                        <ul class="help-info-text c7">\
                            <li>[Repair] Try to use the REPAIR command to repair the damaged table, only a simple repair can be done, if the repair is unsuccessful, please consider using the myisamchk tool</li>\
                            <li>[Optimization] Executing the OPTIMIZE command can reclaim unreleased disk space. It is recommended to execute it once a month</li>\
                            <li>[Convert to InnoDB/MyISAM] Convert the data table engine, it is recommended to convert all tables to InnoDB</li>\
                        </ul></div>'
        });
        tableFixed('database_fix');
    });
}


function setDbMaster(name){
    myPost('set_db_master', {name:name}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
        setTimeout(function(){
            masterOrSlaveConf();
        }, 2000);
    });
}


function setDbSlave(name){
    myPost('set_db_slave', {name:name}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
        setTimeout(function(){
            masterOrSlaveConf();
        }, 2000);
    });
}


function addMasterRepSlaveUser(){
    layer.open({
        type: 1,
        area: '500px',
        title: 'Add sync account',
        closeBtn: 1,
        shift: 5,
        shadeClose: true,
        btn:["Submit","Cancel"],
        content: "<form class='bt-form pd20' id='add_master'>\
            <div class='line'><span class='tname'>Username</span><div class='info-r'><input name='username' class='bt-input-text mr5' placeholder='Username' type='text' style='width:330px;' value='"+(randomStrPwd(6))+"'></div></div>\
            <div class='line'>\
            <span class='tname'>Password</span>\
            <div class='info-r'><input class='bt-input-text mr5' type='text' name='password' id='MyPassword' style='width:330px' value='"+(randomStrPwd(16))+"' /><span title='Random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span></div>\
            </div>\
            <input type='hidden' name='ps' value='' />\
          </form>",
        success:function(){
            $("input[name='name']").keyup(function(){
                var v = $(this).val();
                $("input[name='db_user']").val(v);
                $("input[name='ps']").val(v);
            });

            $('select[name="dataAccess"]').change(function(){
                var v = $(this).val();
                if (v == 'ip'){
                    $(this).after("<input id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                } else {
                    $('#dataAccess_subid').remove();
                }
            });
        },
        yes:function(index){
            var data = $("#add_master").serialize();
            data = decodeURIComponent(data);
            var dataObj = toArrayObject(data);
            if(!dataObj['address']){
                dataObj['address'] = dataObj['dataAccess'];
            }

            myPost('add_master_rep_slave_user', dataObj, function(data){
                var rdata = $.parseJSON(data.data);
                showMsg(rdata.msg,function(){
                    layer.close(index);
                    if (rdata.status){
                        getMasterRepSlaveList();
                    }
                },{icon: rdata.status ? 1 : 2},600);
            });
        }
    });
}



function updateMasterRepSlaveUser(username){

    var index = layer.open({
        type: 1,
        area: '500px',
        title: 'Update account',
        closeBtn: 1,
        shift: 5,
        shadeClose: true,
        content: "<form class='bt-form pd20 pb70' id='update_master'>\
            <div class='line'><span class='tname'>Username</span><div class='info-r'><input name='username' readonly='readonly' class='bt-input-text mr5' placeholder='Username' type='text' style='width:330px;' value='"+username+"'></div></div>\
            <div class='line'>\
            <span class='tname'>Password</span>\
            <div class='info-r'><input class='bt-input-text mr5' type='text' name='password' id='MyPassword' style='width:330px' value='"+(randomStrPwd(16))+"' /><span title='Random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span></div>\
            </div>\
            <input type='hidden' name='ps' value='' />\
            <div class='bt-form-submit-btn'>\
                <button type='button' class='btn btn-success btn-sm btn-title' id='submit_update_master' >Submit</button>\
            </div>\
          </form>",
    });

    $('#submit_update_master').click(function(){
        var data = $("#update_master").serialize();
        data = decodeURIComponent(data);
        var dataObj = toArrayObject(data);
        myPost('update_master_rep_slave_user', data, function(data){
            var rdata = $.parseJSON(data.data);
            showMsg(rdata.msg,function(){
                if (rdata.status){
                    getMasterRepSlaveList();
                }
                $('.layui-layer-close1').click();
            },{icon: rdata.status ? 1 : 2},600);
        });
    });
}

function getMasterRepSlaveUserCmd(username, db=''){
    myPost('get_master_rep_slave_user_cmd', {username:username,db:db}, function(data){
        var rdata = $.parseJSON(data.data);

        if (!rdata['status']){
            layer.msg(rdata['msg']);
            return;
        }

        var cmd = rdata.data['cmd'];

        var loadOpen = layer.open({
            type: 1,
            title: 'Synchronous command',
            area: '500px',
            content:"<form class='bt-form pd20 pb70' id='add_master'>\
            <div class='line' style='word-wrap: break-word;word-break: normal;'>"+cmd+"</div>\
            <div class='bt-form-submit-btn'>\
                <button type='button' class='btn btn-success btn-sm btn-title class-copy-cmd'>Copy</button>\
            </div>\
          </form>",
        });


        copyPass(cmd);
        $('.class-copy-cmd').click(function(){
            copyPass(cmd);
        });
    });
}

function delMasterRepSlaveUser(username){
    myPost('del_master_rep_slave_user', {username:username}, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg);

        $('.layui-layer-close1').click();

        setTimeout(function(){
            getMasterRepSlaveList();
        },1000);
    });
}


function setDbMasterAccess(username){
    myPost('get_db_access','username='+username, function(data){
        var rdata = $.parseJSON(data.data);
        if (!rdata.status){
            layer.msg(rdata.msg,{icon:2,shade: [0.3, '#000']});
            return;
        }

        var index = layer.open({
            type: 1,
            area: '500px',
            title: 'Set database permissions',
            closeBtn: 1,
            shift: 5,
            btn:["Submit","Cancel"],
            shadeClose: true,
            content: "<form class='bt-form pd20' id='set_db_access'>\
                        <div class='line'>\
                            <span class='tname'>Access permission</span>\
                            <div class='info-r '>\
                                <select class='bt-input-text mr5' name='dataAccess' style='width:100px'>\
                                <option value='127.0.0.1'>Localhost</option>\
                                <option value=\"%\">Everyone</option>\
                                <option value='ip'>Spesific IP</option>\
                                </select>\
                            </div>\
                        </div>\
                      </form>",
            success:function(){
                if (rdata.msg == '127.0.0.1'){
                    $('select[name="dataAccess"]').find("option[value='127.0.0.1']").attr("selected",true);
                } else if (rdata.msg == '%'){
                    $('select[name="dataAccess"]').find('option[value="%"]').attr("selected",true);
                } else if ( rdata.msg == 'ip' ){
                    $('select[name="dataAccess"]').find('option[value="ip"]').attr("selected",true);
                    $('select[name="dataAccess"]').after("<input id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                } else {
                    $('select[name="dataAccess"]').find('option[value="ip"]').attr("selected",true);
                    $('select[name="dataAccess"]').after("<input value='"+rdata.msg+"' id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                }

                 $('select[name="dataAccess"]').change(function(){
                    var v = $(this).val();
                    if (v == 'ip'){
                        $(this).after("<input id='dataAccess_subid' class='bt-input-text mr5' type='text' name='address' placeholder='Multiple IPs are separated by commas (,)' style='width: 230px; display: inline-block;'>");
                    } else {
                        $('#dataAccess_subid').remove();
                    }
                });
            },
            yes:function(index){
                var data = $("#set_db_access").serialize();
                data = decodeURIComponent(data);
                var dataObj = toArrayObject(data);
                if(!dataObj['access']){
                    dataObj['access'] = dataObj['dataAccess'];
                    if ( dataObj['dataAccess'] == 'ip'){
                        if (dataObj['address']==''){
                            layer.msg('IP address cannot be empty!',{icon:2,shade: [0.3, '#000']});
                            return;
                        }
                        dataObj['access'] = dataObj['address'];
                    }
                }
                dataObj['username'] = username;
                myPost('set_dbmaster_access', dataObj, function(data){
                    var rdata = $.parseJSON(data.data);
                    showMsg(rdata.msg,function(){
                        layer.close(index);
                    },{icon: rdata.status ? 1 : 2});
                });
            }
        });

    });
}

function getMasterRepSlaveList(){
    var _data = {};
    if (typeof(page) =='undefined'){
        var page = 1;
    }

    _data['page'] = page;
    _data['page_size'] = 10;
    myPost('get_master_rep_slave_list', _data, function(data){
        // console.log(data);
        var rdata = [];
        try {
            rdata = $.parseJSON(data.data);
        } catch(e){
            console.log(e);
        }
        var list = '';
        // console.log(rdata['data']);
        var user_list = rdata['data'];
        for (i in user_list) {
            // console.log(i);
            var name = user_list[i]['username'];
            list += '<tr><td>'+name+'</td>\
                <td>'+user_list[i]['password']+'</td>\
                <td>\
                    <a class="btlink" onclick="updateMasterRepSlaveUser(\''+name+'\');">Modify</a> | \
                    <a class="btlink" onclick="delMasterRepSlaveUser(\''+name+'\');">Delete</a> | \
                    <a class="btlink" onclick="setDbMasterAccess(\''+name+'\');">Permissions</a> | \
                    <a class="btlink" onclick="getMasterRepSlaveUserCmd(\''+name+'\');">Synchronize commands</a>\
                </td>\
            </tr>';
        }

        $('#get_master_rep_slave_list_page tbody').html(list);
        $('.dataTables_paginate_4').html(rdata['page']);
    });
}

function getMasterRepSlaveListPage(){
    var page = '<div class="dataTables_paginate_4 dataTables_paginate paging_bootstrap page" style="margin-top:0px;"></div>';
        page += '<div class="table_toolbar" style="left:0px;"><span class="sync btn btn-default btn-sm" onclick="addMasterRepSlaveUser()" title="">Add sync account</span></div>';

    var loadOpen = layer.open({
        type: 1,
        title: 'Sync account list',
        area: '500px',
        content:"<div class='bt-form pd20 c6'>\
                 <div class='divtable mtb10' id='get_master_rep_slave_list_page'>\
                    <div><table class='table table-hover'>\
                        <thead><tr><th>Username</th><th>Password</th><th>Action</th></tr></thead>\
                        <tbody></tbody>\
                    </table></div>\
                    "+page +"\
                </div>\
            </div>",
        success:function(){
            getMasterRepSlaveList();
        }
    });
}


function deleteSlave(){
    myPost('delete_slave', {}, function(data){
        var rdata = $.parseJSON(data.data);
        showMsg(rdata['msg'], function(){
            masterOrSlaveConf();
        },{},3000);
    });
}


function getFullSyncStatus(db){
    var timeId = null;

    var btn = '<div class="table_toolbar" style="left:0px;"><span data-status="init" class="sync btn btn-default btn-sm" id="begin_full_sync" title="">Start</span></div>';
    var loadOpen = layer.open({
        type: 1,
        title: 'Full synchronization ['+db+']',
        area: '500px',
        content:"<div class='bt-form pd20 c6'>\
                 <div class='divtable mtb10'>\
                    <span id='full_msg'></span>\
                    <div class='progress'>\
                        <div class='progress-bar' role='progressbar' aria-valuenow='0' aria-valuemin='0' aria-valuemax='100' style='min-width: 2em;'>0%</div>\
                    </div>\
                </div>\
                "+btn+"\
            </div>",
        cancel: function(){
            clearInterval(timeId);
        }
    });

    function fullSync(db,begin){

        myPostN('full_sync', {db:db,begin:begin}, function(data){
            var rdata = $.parseJSON(data.data);
            $('#full_msg').text(rdata['msg']);
            $('.progress-bar').css('width',rdata['progress']+'%');
            $('.progress-bar').text(rdata['progress']+'%');

            if (rdata['code']==6 ||rdata['code']<0){
                layer.msg(rdata['msg']);
                clearInterval(timeId);
                $("#begin_full_sync").attr('data-status','init');
            }
        });
    }

    $('#begin_full_sync').click(function(){
        var val = $(this).attr('data-status');
        if (val == 'init'){
            fullSync(db,1);
            timeId = setInterval(function(){
                fullSync(db,0);
            }, 1000);
            $(this).attr('data-status','starting');
        } else {
            layer.msg("Synchronizing..");
        }
    });
}

function addSlaveSSH(ip=''){

    myPost('get_slave_ssh_by_ip', {ip:ip}, function(rdata){

        var rdata = $.parseJSON(rdata.data);

        var ip = '127.0.0.1';
        var port = "22";
        var id_rsa = '';
        var db_user ='';

        if (rdata.data.length>0){
            ip = rdata.data[0]['ip'];
            port = rdata.data[0]['port'];
            id_rsa = rdata.data[0]['id_rsa'];
            db_user = rdata.data[0]['db_user'];
        }

        var index = layer.open({
            type: 1,
            area: ['500px','480px'],
            title: 'Add ssh',
            closeBtn: 1,
            shift: 5,
            shadeClose: true,
            btn:["Submit","Cancel"],
            content: "<form class='bt-form pd20'>\
                <div class='line'><span class='tname'>IP</span><div class='info-r'><input name='ip' class='bt-input-text mr5' type='text' style='width:330px;' value='"+ip+"'></div></div>\
                <div class='line'><span class='tname'>Port</span><div class='info-r'><input name='port' class='bt-input-text mr5' type='number' style='width:330px;' value='"+port+"'></div></div>\
                <div class='line'><span class='tname'>Sync account [DB]</span><div class='info-r'><input name='db_user'  placeholder='If it is empty, take the first one!' class='bt-input-text mr5' type='text' style='width:330px;' value='"+db_user+"'></div></div>\
                <div class='line'>\
                <span class='tname'>ID_RSA</span>\
                <div class='info-r'><textarea class='bt-input-text mr5' row='20' cols='50' name='id_rsa' style='width:330px;height:200px;'></textarea></div>\
                </div>\
                <input type='hidden' name='ps' value='' />\
              </form>",
            success:function(){
                $('textarea[name="id_rsa"]').html(id_rsa);
            },
            yes:function(index){
                var ip = $('input[name="ip"]').val();
                var port = $('input[name="port"]').val();
                var db_user = $('input[name="db_user"]').val();
                var id_rsa = $('textarea[name="id_rsa"]').val();

                var data = {ip:ip,port:port,id_rsa:id_rsa,db_user:db_user};
                myPost('add_slave_ssh', data, function(data){
                    layer.close(index);
                    var rdata = $.parseJSON(data.data);
                    showMsg(rdata.msg,function(){
                        if (rdata.status){
                            getSlaveSSHPage();
                        }
                    },{icon: rdata.status ? 1 : 2},600);
                });
            }
        });
    });
}



function delSlaveSSH(ip){
    myPost('del_slave_ssh', {ip:ip}, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        showMsg(rdata.msg,function(){
            if (rdata.status){
                getSlaveSSHPage();
            }
        },{icon: rdata.status ? 1 : 2}, 600);
    });
}


function delSlaveSyncUser(ip){
    myPost('del_slave_sync_user', {ip:ip}, function(rdata){
        var rdata = $.parseJSON(rdata.data);
        showMsg(rdata.msg,function(){
            if (rdata.status){
                getSlaveSyncUserPage();
            }
        },{icon: rdata.status ? 1 : 2}, 600);
    });
}

function getSlaveSSHPage(page=1){
    var _data = {};
    _data['page'] = page;
    _data['page_size'] = 5;
    _data['tojs'] ='getSlaveSSHPage';
    myPost('get_slave_ssh_list', _data, function(data){
        var layerId = null;
        var rdata = [];
        try {
            rdata = $.parseJSON(data.data);
        } catch(e) {
            console.log(e);
        }
        var list = '';
        var ssh_list = rdata['data'];
        for (i in ssh_list) {
            var ip = ssh_list[i]['ip'];
            var port = ssh_list[i]['port'];

            var id_rsa = 'Not set';
            if ( ssh_list[i]['port'] != ''){
                id_rsa = 'Has been set';
            }

            var db_user = 'Not set';
            if ( ssh_list[i]['db_user'] != ''){
                db_user = ssh_list[i]['db_user'];
            }

            list += '<tr><td>'+ip+'</td>\
                <td>'+port+'</td>\
                <td>'+db_user+'</td>\
                <td>'+id_rsa+'</td>\
                <td>\
                    <a class="btlink" onclick="addSlaveSSH(\''+ip+'\');">Modify</a> | \
                    <a class="btlink" onclick="delSlaveSSH(\''+ip+'\');">Delete</a>\
                </td>\
            </tr>';
        }

        $('.get-slave-ssh-list tbody').html(list);
        $('.dataTables_paginate_4').html(rdata['page']);
    });
}

function addSlaveSyncUser(ip=''){

    myPost('get_slave_sync_user_by_ip', {ip:ip}, function(rdata){

        var rdata = $.parseJSON(rdata.data);

        var ip = '127.0.0.1';
        var port = "22";
        var cmd = '';
        var user = 'input_sync_user';
        var pass = 'input_sync_pwd';
        var mode = '0';

        if (rdata.data.length>0){
            ip = rdata.data[0]['ip'];
            port = rdata.data[0]['port'];
            cmd = rdata.data[0]['cmd'];
            user = rdata.data[0]['user'];
            pass = rdata.data[0]['pass'];
            mode = rdata.data[0]['mode'];
        }

        var index = layer.open({
            type: 1,
            area: ['500px','470px'],
            title: 'Sync account',
            closeBtn: 1,
            shift: 5,
            shadeClose: true,
            btn:["Submit","Cancel"],
            content: "<form class='bt-form pd20'>\
                <div class='line'><span class='tname'>IP</span><div class='info-r'><input name='ip' class='bt-input-text mr5' type='text' style='width:330px;' value='"+ip+"'></div></div>\
                <div class='line'><span class='tname'>Port</span><div class='info-r'><input name='port' class='bt-input-text mr5' type='number' style='width:330px;' value='"+port+"'></div></div>\
                <div class='line'><span class='tname'>Sync account</span><div class='info-r'><input name='user' class='bt-input-text mr5' type='text' style='width:330px;' value='"+user+"'></div></div>\
                <div class='line'><span class='tname'>Sync password</span><div class='info-r'><input name='pass' class='bt-input-text mr5' type='text' style='width:330px;' value='"+pass+"'></div></div>\
                <div class='line'>\
                <span class='tname'>CMD [required]</span>\
                <div class='info-r'><textarea class='bt-input-text mr5' row='20' cols='30' name='cmd' style='width:330px;height:150px;'></textarea></div>\
                </div>\
                <input type='hidden' name='mode' value='"+mode+"' />\
              </form>",
            success:function(){
                $('textarea[name="cmd"]').html(cmd);

                $('textarea[name="cmd"]').change(function(){
                    var val = $(this).val();
                    var vlist = val.split(',');
                    var a = {};
                    for (var i in vlist) {
                        var tmp = toTrim(vlist[i]);
                        var tmp_a = tmp.split(" ");
                        var real_tmp = tmp_a[tmp_a.length-1];
                        var kv = real_tmp.split("=");
                        a[kv[0]] = kv[1].replace("'",'').replace("'",'');
                    }

                    $('input[name="ip"]').val(a['MASTER_HOST']);
                    $('input[name="port"]').val(a['MASTER_PORT']);
                    $('input[name="user"]').val(a['MASTER_USER']);
                    $('input[name="pass"]').val(a['MASTER_PASSWORD']);

                    console.log(a['MASTER_USE_GTID'],typeof(a['MASTER_USE_GTID']));
                    if (typeof(a['MASTER_USE_GTID']) != 'undefined' ){
                        $('input[name="mode"]').val('1');
                    }
                });
            },
            yes:function(index){
                var ip = $('input[name="ip"]').val();
                var port = $('input[name="port"]').val();
                var user = $('input[name="user"]').val();
                var pass = $('input[name="pass"]').val();
                var cmd = $('textarea[name="cmd"]').val();
                var mode = $('input[name="mode"]').val();

                var data = {ip:ip,port:port,cmd:cmd,user:user,pass:pass,mode:mode};
                myPost('add_slave_sync_user', data, function(ret_data){
                    layer.close(index);
                    var rdata = $.parseJSON(ret_data.data);
                    showMsg(rdata.msg,function(){
                        if (rdata.status){
                            getSlaveSyncUserPage();
                        }
                    },{icon: rdata.status ? 1 : 2},600);
                });
            }
        });
    });
}

function getSlaveSyncUserPage(page=1){
    var _data = {};
    _data['page'] = page;
    _data['page_size'] = 5;
    _data['tojs'] ='getSlaveSyncUserPage';
    myPost('get_slave_sync_user_list', _data, function(data){
        var layerId = null;
        var rdata = [];
        try {
            rdata = $.parseJSON(data.data);
        } catch(e) {
            console.log(e);
        }

        var list = '';
        var user_list = rdata['data'];
        for (i in user_list) {
            var ip = user_list[i]['ip'];
            var port = user_list[i]['port'];
            var user = user_list[i]['user'];
            var apass = user_list[i]['pass'];

            var cmd = 'Not set';
            if (user_list[i]['cmd']!=''){
                cmd = 'Has been set';
            }

            list += '<tr><td>'+ip+'</td>\
                <td>'+port+'</td>\
                <td>'+user+'</td>\
                <td>'+apass+'</td>\
                <td>'+cmd+'</td>\
                <td>\
                    <a class="btlink" onclick="addSlaveSyncUser(\''+ip+'\');">Modify</a> | \
                    <a class="btlink" onclick="delSlaveSyncUser(\''+ip+'\');">Delete</a>\
                </td>\
            </tr>';
        }

        $('.get-slave-ssh-list tbody').html(list);
        $('.dataTables_paginate_4').html(rdata['page']);
    });
}

function getSlaveCfg(){

    myPost('get_slave_sync_mode', '', function(data){
        var rdata = $.parseJSON(data.data);
        var mode_none = 'success';
        var mode_ssh = 'danger';
        var mode_sync_user = 'danger';
        if(rdata.status){
            var mode_none = 'danger';
            if (rdata.data == 'ssh'){
                var mode_ssh = 'success';
                var mode_sync_user = 'danger';
            } else {
                var mode_ssh = 'danger';
                var mode_sync_user = 'success';
            }
        }

        layerId = layer.open({
            type: 1,
            title: 'Sync configuration',
            area: ['400px','180px'],
            content:"<div class='bt-form pd20 c6'>\
                    <p class='conf_p'>\
                        <span class='f14 c6 mr20'>Current synchronization mode from the library</span>\
                        <b class='f14 c6 mr20'></b>\
                        <button class='btn btn-"+mode_none+" btn-xs slave-db-mode btn-none'>None</button>\
                        <button class='btn btn-"+mode_ssh+" btn-xs slave-db-mode btn-ssh'>SSH</button>\
                        <button class='btn btn-"+mode_sync_user+" btn-xs slave-db-mode btn-sync-user'>Sync account</button>\
                    </p>\
                    <hr />\
                    <p class='conf_p'>\
                        <span class='f14 c6 mr20'>Configuration settings</span>\
                        <b class='f14 c6 mr20'></b>\
                        <button class='btn btn-success btn-xs btn-slave-ssh'>SSH</button>\
                        <button class='btn btn-success btn-xs btn-slave-user'>Sync account</button>\
                    </p>\
                </div>",
            success:function(){
                $('.btn-slave-ssh').click(function(){
                    getSlaveSSHList();
                });

                $('.btn-slave-user').click(function(){
                    getSlaveUserList();
                });

                $('.slave-db-mode').click(function(){
                    var _this = this;
                    var mode = 'none';
                    if ($(this).hasClass('btn-ssh')){
                        mode = 'ssh';
                    }
                    if ($(this).hasClass('btn-sync-user')){
                        mode = 'sync-user';
                    }

                    myPost('set_slave_sync_mode', {mode:mode}, function(data){
                        var rdata = $.parseJSON(data.data);
                        showMsg(rdata.msg,function(){
                            $('.slave-db-mode').remove('btn-success').addClass('btn-danger');
                            $(_this).removeClass('btn-danger').addClass('btn-success');
                        },{icon:rdata.status?1:2},2000);
                    });

                });
            }
        });
    });
}

function getSlaveUserList(){

    var page = '<div class="dataTables_paginate_4 dataTables_paginate paging_bootstrap page" style="margin-top:0px;"></div>';
    page += '<div class="table_toolbar" style="left:0px;"><span class="sync btn btn-default btn-sm" onclick="addSlaveSyncUser()" title="">Add sync account</span></div>';

    layerId = layer.open({
        type: 1,
        title: 'Sync account list',
        area: '500px',
        content:"<div class='bt-form pd20 c6'>\
                 <div class='divtable mtb10'>\
                    <div><table class='table table-hover get-slave-ssh-list'>\
                        <thead><tr><th>IP</th><th>PORT</th><th>Sync account</th><th>Sync password</th><th>CMD</th><th>Action</th></tr></thead>\
                        <tbody></tbody>\
                    </table></div>\
                    "+page +"\
                </div>\
            </div>",
        success:function(){
            getSlaveSyncUserPage(1);
        }
    });
}

function getSlaveSSHList(page=1){

    var page = '<div class="dataTables_paginate_4 dataTables_paginate paging_bootstrap page" style="margin-top:0px;"></div>';
    page += '<div class="table_toolbar" style="left:0px;"><span class="sync btn btn-default btn-sm" onclick="addSlaveSSH()" title="">Add ssh</span></div>';

    layerId = layer.open({
        type: 1,
        title: 'SSH List',
        area: '500px',
        content:"<div class='bt-form pd20 c6'>\
                 <div class='divtable mtb10'>\
                    <div><table class='table table-hover get-slave-ssh-list'>\
                        <thead><tr><th>IP</th><th>PORT</th><th>Sync account</th><th>SSH</th><th>Action</th></tr></thead>\
                        <tbody></tbody>\
                    </table></div>\
                    "+page +"\
                </div>\
            </div>",
        success:function(){
            getSlaveSSHPage(1);
        }
    });
}

function handlerRun(){
    myPostN('get_slave_sync_cmd', {}, function(data){
        var rdata = $.parseJSON(data.data);
        var cmd = rdata['data'];
        var loadOpen = layer.open({
            type: 1,
            title: 'Manual execution',
            area: '500px',
            content:"<form class='bt-form pd20 pb70' id='add_master'>\
            <div class='line'>"+cmd+"</div>\
            <div class='bt-form-submit-btn'>\
                <button type='button' class='btn btn-success btn-sm btn-title class-copy-cmd'>Copy</button>\
            </div>\
          </form>",
        });
        copyPass(cmd);
        $('.class-copy-cmd').click(function(){
            copyPass(cmd);
        });
    });
}

function initSlaveStatus(){
    myPost('init_slave_status', '', function(data){
        var rdata = $.parseJSON(data.data);
        showMsg(rdata.msg,function(){
            if (rdata.status){
                masterOrSlaveConf();
            }
        },{icon:rdata.status?1:2},2000);
    });
}

function masterOrSlaveConf(version=''){

    function getMasterDbList(){
        var _data = {};
        if (typeof(page) =='undefined'){
            var page = 1;
        }

        _data['page'] = page;
        _data['page_size'] = 10;

        myPost('get_masterdb_list', _data, function(data){
            var rdata = $.parseJSON(data.data);
            var list = '';
            for(i in rdata.data){
                list += '<tr>';
                list += '<td>' + rdata.data[i]['name'] +'</td>';
                list += '<td>' + (rdata.data[i]['master']?'Yes':'No') +'</td>';
                list += '<td style="text-align:right">' +
                    '<a href="javascript:;" class="btlink" onclick="setDbMaster(\''+rdata.data[i]['name']+'\')" title="Join or quit">'+(rdata.data[i]['master']?'Exit':'Join')+'</a> | ' +
                    '<a href="javascript:;" class="btlink" onclick="getMasterRepSlaveUserCmd(\'\',\''+rdata.data[i]['name']+'\')" title="Synchronous command">Synchronous command</a>' +
                '</td>';
                list += '</tr>';
            }

            var con = '<div class="divtable mtb10">\
                    <div class="tablescroll">\
                        <table id="DataBody" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0" style="border: 0 none;">\
                        <thead><tr>\
                        <th>Database name</th>\
                        <th>Synchronize</th>\
                        <th style="text-align:right;">Action</th></tr></thead>\
                        <tbody>\
                        '+ list +'\
                        </tbody></table>\
                    </div>\
                    <div id="databasePage" class="dataTables_paginate paging_bootstrap page"></div>\
                    <div class="table_toolbar" style="left:0px;">\
                        <span class="sync btn btn-default btn-sm" onclick="getMasterRepSlaveListPage()" title="">Sync account list</span>\
                    </div>\
                </div>';

            $(".table_master_list").html(con);
            $('#databasePage').html(rdata.page);
        });
    }

    function getAsyncMasterDbList(){
        var _data = {};
        if (typeof(page) =='undefined'){
            var page = 1;
        }

        _data['page'] = page;
        _data['page_size'] = 10;

        myPost('get_slave_list', _data, function(data){
            var rdata = $.parseJSON(data.data);
            var list = '';
            for(i in rdata.data){

                var v = rdata.data[i];
                var status = "<a class='btlink db_error'>Abnormal</>";
                if (v['Slave_SQL_Running'] == 'Yes' && v['Slave_IO_Running'] == 'Yes'){
                    status = "Normal";
                }

                list += '<tr>';
                list += '<td>' + rdata.data[i]['Master_Host'] +'</td>';
                list += '<td>' + rdata.data[i]['Master_Port'] +'</td>';
                list += '<td>' + rdata.data[i]['Master_User'] +'</td>';
                list += '<td>' + rdata.data[i]['Master_Log_File'] +'</td>';
                list += '<td>' + rdata.data[i]['Slave_IO_Running'] +'</td>';
                list += '<td>' + rdata.data[i]['Slave_SQL_Running'] +'</td>';
                list += '<td>' + status +'</td>';
                list += '<td style="text-align:right">' +
                    '<a href="javascript:;" class="btlink" onclick="deleteSlave()" title="Delete">Delete</a>' +
                '</td>';
                list += '</tr>';
            }

            var con = '<div class="divtable mtb10">\
                    <div class="tablescroll">\
                        <table id="DataBody" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0" style="border: 0 none;">\
                        <thead><tr>\
                        <th>Master [service]</th>\
                        <th>Port</th>\
                        <th>User</th>\
                        <th>Log</th>\
                        <th>IO</th>\
                        <th>SQL</th>\
                        <th>Status</th>\
                        <th style="text-align:right;">Action</th></tr></thead>\
                        <tbody>\
                        '+ list +'\
                        </tbody></table>\
                    </div>\
                </div>';

            $(".table_slave_status_list").html(con);

            $('.db_error').click(function(){
                layer.open({
                    type: 1,
                    title: 'Synchronization exception information',
                    area: '500px',
                    content:"<form class='bt-form pd20 pb70'>\
                    <div class='line'>"+v['Error']+"</div>\
                    <div class='bt-form-submit-btn'>\
                        <button type='button' class='btn btn-success btn-sm btn-title class-copy-db-err'>Copy</button>\
                    </div>\
                  </form>",
                    success:function(){
                        copyText(v['Error']);
                        $('.class-copy-db-err').click(function(){
                            copyText(v['Error']);
                        });
                    }
                });
            });
        });
    }

    function getAsyncDataList(){
        var _data = {};
        if (typeof(page) =='undefined'){
            var page = 1;
        }

        _data['page'] = page;
        _data['page_size'] = 10;
        myPost('get_masterdb_list', _data, function(data){
            var rdata = $.parseJSON(data.data);
            var list = '';
            for(i in rdata.data){
                list += '<tr>';
                list += '<td>' + rdata.data[i]['name'] +'</td>';
                list += '<td style="text-align:right">' +
                    '<a href="javascript:;" class="btlink" onclick="setDbSlave(\''+rdata.data[i]['name']+'\')"  title="Join|Exit">'+(rdata.data[i]['slave']?'Exit':'Join')+'</a> | ' +
                    '<a href="javascript:;" class="btlink" onclick="getFullSyncStatus(\''+rdata.data[i]['name']+'\')" title="Synchronize">Synchronize</a>' +
                '</td>';
                list += '</tr>';
            }

            var con = '<div class="divtable mtb10">\
                    <div class="tablescroll">\
                        <table id="DataBody" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0" style="border: 0 none;">\
                        <thead><tr>\
                        <th>Local library name</th>\
                        <th style="text-align:right;">Action</th></tr></thead>\
                        <tbody>\
                        '+ list +'\
                        </tbody></table>\
                    </div>\
                    <div id="databasePage" class="dataTables_paginate paging_bootstrap page"></div>\
                    <div class="table_toolbar" style="left:0px;">\
                        <span class="sync btn btn-default btn-sm" onclick="handlerRun()" title="After the login-free setting, you need to manually execute it!">Manual command</span>\
                        <span class="sync btn btn-default btn-sm" onclick="getFullSyncStatus(\'ALL\')" title="Full sync">Full sync</span>\
                    </div>\
                </div>';

            $(".table_slave_list").html(con);
            $('#databasePage').html(rdata.page);
        });
    }



    function getMasterStatus(){
        myPost('get_master_status', '', function(rdata){
            var rdata = $.parseJSON(rdata.data);
            // console.log('mode:',rdata.data);
            if ( typeof(rdata.status) != 'undefined' && !rdata.status && rdata.data == 'pwd'){
                layer.msg(rdata.msg, {icon:2});
                return;
            }

            var rdata = rdata.data;
            var limitCon = '\
                <p class="conf_p">\
                    <span class="f14 c6 mr20">Master-Slave synchronous mode</span><span class="f14 c6 mr20"></span>\
                    <button class="btn '+(!(rdata.mode == "classic") ? 'btn-danger' : 'btn-success')+' btn-xs db-mode btn-classic">Classic</button>\
                    <button class="btn '+(!(rdata.mode == "gtid") ? 'btn-danger' : 'btn-success')+' btn-xs db-mode btn-gtid">GTID</button>\
                </p>\
                <hr/>\
                <p class="conf_p">\
                    <span class="f14 c6 mr20">Master [main] configuration</span><span class="f14 c6 mr20"></span>\
                    <button class="btn '+(!rdata.status ? 'btn-danger' : 'btn-success')+' btn-xs btn-master">'+(!rdata.status ? 'Unopened' : 'Opened') +'</button>\
                </p>\
                <hr/>\
                <!-- master list -->\
                <div class="safe bgw table_master_list"></div>\
                <hr/>\
                <!-- class="conf_p" -->\
                <p class="conf_p">\
                    <span class="f14 c6 mr20">Slave [from] configuration</span><span class="f14 c6 mr20"></span>\
                    <button class="btn '+(!rdata.slave_status ? 'btn-danger' : 'btn-success')+' btn-xs btn-slave">'+(!rdata.slave_status ? 'Stopped' : 'Started') +'</button>\
                    <button class="btn btn-success btn-xs" onclick="getSlaveCfg()" >Sync configuration</button>\
                    <button class="btn btn-success btn-xs" onclick="initSlaveStatus()" >Snitialization</button>\
                </p>\
                <hr/>\
                <!-- slave status list -->\
                <div class="safe bgw table_slave_status_list"></div>\
                <!-- slave list -->\
                <div class="safe bgw table_slave_list"></div>\
                ';
            $(".soft-man-con").html(limitCon);

            $(".btn-master").click(function () {
                myPost('set_master_status', 'close=change', function(data){
                    var rdata = $.parseJSON(data.data);
                    layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                    setTimeout(function(){
                        getMasterStatus();
                    }, 3000);
                });
            });

            $(".btn-slave").click(function () {
                myPost('set_slave_status', 'close=change', function(data){
                    var rdata = $.parseJSON(data.data);
                    layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                    setTimeout(function(){
                        getMasterStatus();
                    }, 3000);
                });
            });

            $('.db-mode').click(function(){
                if ($(this).hasClass('btn-success')){
                    //no action
                    return;
                }

                var mode = 'classic';
                if ($(this).hasClass('btn-gtid')){
                    mode = 'gtid';
                }

                layer.open({
                    type:1,
                    title:"MaridDB master-slave mode switching",
                    shadeClose:false,
                    btnAlign: 'c',
                    btn: ['Switch and reboot', 'Switch without reboot'],
                    yes: function(index, layero){
                        this.change(index,mode,"yes");

                    },
                    btn2: function(index, layero){
                        this.change(index,mode,"no");
                        return false;
                    },
                    change:function(index,mode,reload){
                        console.log(index,mode,reload);
                        myPost('set_dbrun_mode',{'mode':mode,'reload':reload},function(data){
                            layer.close(index);
                            var rdata = $.parseJSON(data.data);
                            showMsg(rdata.msg ,function(){
                                getMasterStatus();
                            },{ icon: rdata.status ? 1 : 5 });
                        });
                    }
                });
            });

            if (rdata.status){
                getMasterDbList();
            }

            // if (rdata.slave_status){
                getAsyncMasterDbList();
                getAsyncDataList()
            // }
        });
    }
    getMasterStatus();
}

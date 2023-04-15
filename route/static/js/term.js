function Terms (el, config) {
  if (typeof config == "undefined") config = {};
  this.el = el;
  this.id = config.ssh_info.id || '';
  this.bws = null;
  this.route = '/webssh';
  this.term = null;
  this.info = null;
  this.last_body = null;
  this.fontSize = 15;
  this.ssh_info = config.ssh_info;
  this.run();
}
Terms.prototype = {
  connect: function (callback) {
      var that = this;
      if (!this.bws || this.bws.readyState == 3 || this.bws.readyState == 2) {
          this.bws = new WebSocket((window.location.protocol === 'http:' ? 'ws://' : 'wss://') + window.location.host + this.route);
          this.bws.addEventListener('message', function (ev) { that.on_message(ev) });
          this.bws.addEventListener('close', function (ev) { that.on_close(ev) });
          this.bws.addEventListener('error', function (ev) { that.on_error(ev) });
          this.bws.addEventListener('open', function (ev) { that.on_open(ev) });
          if (callback) callback(this.bws)
      }
  },

  on_open: function (ws_event) {
      var http_token = $("#request_token_head").attr('token');
      this.ssh_info['x-http-token'] = http_token;

      this.send(JSON.stringify(this.ssh_info || { 'x-http-token': http_token }))
      this.term.FitAddon.fit();
      this.resize({ cols: this.term.cols, rows: this.term.rows });
  },
  on_message: function (ws_event) {
      result = ws_event.data;
      if (!result) return;
      that = this;
      if ((result.indexOf("@127.0.0.1:") != -1 || result.indexOf("@localhost:") != -1) && result.indexOf('Authentication failed') != -1) {
          that.term.write(result);
          host_trem.localhost_login_form(result);
          that.close();
          return;
      }
      if (result.length > 1 && that.last_body === false) {
          that.last_body = true;
      }
      that.term.write(result);
      that.set_term_icon(1);
      if (result == '\r\signout\r\n' || result == 'signout\r\n' || result == '\r\nlogout\r\n' || result == 'logout\r\n') {
          that.close();
          that.bws = null;

      }
  },

  on_close: function (ws_event) {
      this.set_term_icon(0);
      this.bws = null;
  },

  set_term_icon: function (status) {
      var icon_list = ['icon-warning', 'icon-sucess', 'icon-info'];
      if (status == 1) {
          if ($("[data-id='" + this.id + "']").attr("class").indexOf('active') == -1) {
              status = 2;
          }
      }
      $("[data-id='" + this.id + "']").find('.icon').removeAttr('class').addClass(icon_list[status] + ' icon');
      if (status == 2) {
          that = this;
          setTimeout(function () {
              $("[data-id='" + that.id + "']").find('.icon').removeAttr('class').addClass(icon_list[1] + ' icon');
          }, 200);
      }
  },


  on_error: function (ws_event) {
      if (ws_event.target.readyState === 3) {
      } else {
          console.log(ws_event)
      }
  },
  send: function (data, num) {
      var that = this;
      if (!this.bws || this.bws.readyState == 3 || this.bws.readyState == 2) {
          this.connect();
      }
      if (this.bws.readyState === 1) {
          this.bws.send(data);
      } else {
          if (this.state === 3) return;
          if (!num) num = 0;
          if (num < 5) {
              num++;
              setTimeout(function () { that.send(data, num++); }, 100)
          }
      }
  },

  close: function () {
      this.bws.close();
      this.set_term_icon(0);
  },
  resize: function (size) {
      if (this.bws) {
          size['resize'] = 1;
          this.send(JSON.stringify(size));
      }

  },
  run: function (ssh_info) {
      var that = this;
      this.term = new Terminal({ fontSize: this.fontSize, screenKeys: true, useStyle: true });
      this.term.setOption('cursorBlink', true);
      this.last_body = false;
      this.term.open($(this.el)[0]);

      // this.term.FitAddon = new window.FitAddon();
      // this.term.loadAddon(this.term.FitAddon);
      // this.term.WebLinksAddon = new WebLinksAddon.WebLinksAddon();
      // this.term.loadAddon(this.term.WebLinksAddon);
      if (ssh_info) this.ssh_info = ssh_info;
      this.connect();
      that.term.onData(function (data) {
          try {
              that.bws.send(data);
          } catch (e) {
              that.term.write('\r\nConnection lost, trying to reconnect!\r\n');
              that.connect();
          }
      });
      this.term.focus();
  }
}

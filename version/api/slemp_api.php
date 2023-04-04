<?php

class slempApi {
    private $SLEMP_KEY   = "j7GQhzNcBV4KU9QKYPXvtjSzCcmfkc0e";
    private $SLEMP_PANEL = "http://127.0.0.1:7200";

    public function __construct($slemp_panel = null, $slemp_key = null) {
        if ($slemp_panel) {
            $this->SLEMP_PANEL = $slemp_panel;
        }

        if ($slemp_key) {
            $this->SLEMP_KEY = $slemp_key;
        }
    }

    private function httpPostCookie($url, $data, $timeout = 60) {
        $cookie_file = './' . md5($this->SLEMP_PANEL) . '.cookie';
        if (!file_exists($cookie_file)) {
            $fp = fopen($cookie_file, 'w+');
            fclose($fp);
        }

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_setopt($ch, CURLOPT_COOKIEJAR, $cookie_file);
        curl_setopt($ch, CURLOPT_COOKIEFILE, $cookie_file);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_HEADER, 0);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        $output = curl_exec($ch);
        curl_close($ch);
        return $output;
    }

    private function getKeyData() {
        $now_time   = time();
        $ready_data = array(
            'request_token' => md5($now_time . '' . md5($this->SLEMP_KEY)),
            'request_time'  => $now_time,
        );
        return $ready_data;
    }

    public function getLogsList() {
        $url = $this->SLEMP_PANEL . '/api/firewall/get_log_list';

        $post_data          = $this->getKeyData();
        $post_data['p']     = '1';
        $post_data['limit'] = 10;

        $result = $this->httpPostCookie($url, $post_data);

        $data = json_decode($result, true);
        return $data;
    }

}

$api = new slempApi();
$rdata = $api->getLogsList();

// var_dump($rdata);
echo json_encode($rdata);

?>

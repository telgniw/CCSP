<?php
  require('facebook.php');
  $APP_TITLE = 'PhotoViewer';
  
  $API_KEY = '76d2bf4b6c263ba6bbc83913cdc73f7f';
  $APP_ID = '187338287983261';
  $APP_SECRET = 'c4ba9997293da82f9636b09df4f7c4e7';
  $FB = new Facebook(array(
    'appId'  => $APP_ID,
    'secret' => $APP_SECRET,
    'cookie' => true,
  ));

  $perms = 'user_photos,user_photo_video_tags,friends_photos,friends_photo_video_tags,publish_stream';
  $session = $FB->getSession();
  try {
    $user = $FB->getUser();
    $me = $FB->api('/me');
  } catch (FacebookApiException $e) {
    $user = null;
    $me = null;
  }

  $loginUrl = $FB->getLoginUrl(array(
    'scope' => $perms
  ));

  $url = urlencode('http://'.$_SERVER['SERVER_NAME'].$_SERVER['REQUEST_URI']);
  $appUrl = urlencode('http://www.facebook.com/apps/application.php?id='.$APP_ID);
  $img = urlencode('http://'.$_SERVER['SERVER_NAME'].'/img/icon.png');
  $shareUrl = "http://www.facebook.com/dialog/feed?app_id=$APP_ID&redirect_uri=$url&link=$appUrl&picture=$img&access_token=$access";
?>

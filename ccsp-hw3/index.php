<!DOCTYPE html>
<?php
  require_once('php/common.php');
?>
<html>
<head>
  <meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=0;">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title><?php echo $APP_TITLE; ?> by 易</title>
  <link rel="icon" href="favicon.ico">
  <style type="text/css" media="handheld">@import "iui/iui.css";</style>
  <style type="text/css" media="screen">@import "iui/iui-screen.css";</style>
  <script type="text/javascript" src="iui/iui.js"></script>
  <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js"></script>
</head>
<body>
  <div class="toolbar">
    <h1 id="pageTitle"></h1>
    <a id="backButton" class="button" href="#"></a>
    <?php if(!$me): ?>
    <a id="loginButton" class="buttonImg" href="<?php echo $loginUrl; ?>" target="_self"><img src="img/fb_login.png"></a>
    <?php else: ?>
    <a id="shareButton" class="buttonImg" href="<?php echo $shareUrl; ?>" target="_self"><img src="img/fb_share.png"></a>
    <?php endif ?>
  </div>
  <ul id="home" title="Home" selected="true">
    <li><a href="#about">About <?php echo $APP_TITLE; ?></a></li>
    <?php if(!$me): ?>
    <?php else: ?>
    <li><a href="view.php" target="_self">View Your Photos</a></li>
    <?php endif ?>
  </ul>
  <div id="about" title="About <?php echo $APP_TITIE; ?>" class="panel">
    <h2>What is <?php echo $APP_TITLE; ?>?</h2>
    <fieldset>This is my homework 3 for Cloud Computing Service Programming Class ;)</fieldset>
    <h2>Who am I?</h2>
    <fieldset>I'm Yi Huang.</fieldset>
    <h2>Like <?php echo $APP_TITLE; ?>? <iframe src="http://www.facebook.com/plugins/like.php?app_id=<?php echo $APP_ID; ?>&href=<?php echo $appUrl; ?>&layout=button_count&width=450&show_faces=true&height=21" scrolling="no" frameborder="0" style="border:none; overflow:hidden; width:450px; height:21px;" allowTransparency="true"></iframe></h2>
    <fieldset>
      <span><a href="<?php echo $shareUrl; ?>" target="_self"><img src="img/fb_share.png" align="middle"></a> with your friends!</span>
    </fieldset>
  </div>
</body>
</html>

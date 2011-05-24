<!DOCTYPE html>
<?php
  require_once('php/common.php');
  if(!$user) {
    $photos = null;
  } else {
    $friends = $FB->api('/me/friends', Array(
      'fields' => 'id'
    ));
    $friends = $friends['data'];
    $friend_list = Array(
      $user => true
    );
    foreach($friends as $i => $friend) {
      $friend_list[$friend['id']] = true;
    }
    $photos = $FB->api('/me/photos', Array(
      'fields' => 'id,tags,picture,source'
    ));
    $photos = $photos['data'];
    $counts = Array();
    foreach($photos as $i => $photo) {
      $tags = $photo['tags']['data'];
      foreach($tags as $j => $tag) {
        $id = $tag['id'];
        if(!$friend_list[$id])
          continue;
        if($counts[$id]) {
          $counts[$id] += 1;
        } else {
          $counts[$id] = 1;
          $rphotos[$id] = Array();
          $profile[$id] = $FB->api("/$id");
        }
        array_push($rphotos[$id], $photo);
      }
    }
    arsort($counts);
  }
?>
<head>
  <meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=0;">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title><?php echo $APP_TITLE; ?> by 易</title>
  <style type="text/css" media="screen">@import "iui/iui.css";</style>
  <script type="text/javascript" src="iui/iui.js"></script>
  <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.5.2/jquery.min.js"></script>
</head>
<body>
  <script type="text/javascript">
    var load = function(img_list) {
      for(i in img_list) {
        if(img_list[i].id) {
          document.write('<span><a href="#' + img_list[i].id + '">');
          document.write('<img src="' + img_list[i].src + '">');
          document.write('</a></span>');
        }
      }
    };
  </script>
  <div class="toolbar">
    <h1 id="pageTitle"></h1>
    <a id="backButton" class="button" href="#"></a>
    <?php if(!$user) { ?>
    <a id="loginButton" class="buttonImg" href="<?php echo $loginUrl; ?>" target="_self"><img src="img/fb_login.png"></a>
    <?php } else { ?>
    <a id="shareButton" class="buttonImg" href="<?php echo $shareUrl; ?>" target="_self"><img src="img/fb_share.png"></a>
    <?php } ?>
  </div>
  <ul id="view" title="<?php echo $APP_TITLE; ?>" selected="true">
    <?php
    if($photos) {
      foreach($counts as $id => $count) {
    ?>
    <li><a href="#<?php echo $id; ?>">
      <img src="http://graph.facebook.com/<?php echo $id; ?>/picture">
      <?php echo $profile[$id]['name']; ?><?php echo " ($count)"; ?>
    </a></li>
    <?php
      }
    }
    ?>
  </ul>
  <?php
  if($photos) {
    foreach($counts as $id => $count) {
  ?>
  <div id="<?php echo $id; ?>" title="<?php echo $profile[$id]['name']; ?>" class="panel">
    <fieldset>
      <img src="http://graph.facebook.com/<?php echo $id; ?>/picture">
      <?php echo $profile[$id]['name']; ?>
    </fieldset>
    <fieldset>
      <script type="text/javascript">
        var img_list = [
        <?php
        foreach($rphotos[$id] as $i => $photo) {
          $pid = $photo['id'];
          $psrc = $photo['picture'];
          echo "{ id: '$pid', src: '$psrc' }, ";
        }
        ?>
        ];
        load(img_list);
      </script>
    </fieldset>
  </div>
  <?php
    }
    foreach($photos as $i => $photo) {
  ?>
  <div id="<?php echo $photo['id']; ?>" title="Photo" class="panel">
    <fieldset>
      <img src="<?php echo $photo['source']; ?>">
    </fieldset>
  </div>
  <?php
    }
  }
  ?>
</body>

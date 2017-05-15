/*
 * Placeholder file for plumbum application client logic
 */

import jQuery from 'jquery';
import './scrolling-tabs';

const $ = jQuery;

$(function() {

  // Enable bootstrap tooltips
  $('[title]').tooltip({
    delay: {
      show: 500,
      hide: 100,
    },
  });

  $(document).trigger('init.scrolling-tabs');
});

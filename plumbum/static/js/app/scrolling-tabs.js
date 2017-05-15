import $ from 'jquery';

const hideEndFade = ($scrollingTabs) => {
  return $scrollingTabs.each((idx, el) => {
    const $el = $(el);
    return $el.siblings('.fade-right').toggleClass('scrolling', $el.width() < $el.prop('scrollWidth'));
  });
};

$(document).on('init.scrolling-tabs', () => {
  const $scrollingTabs = $('.scrolling-tabs').not('.is-initialized');
  $scrollingTabs.addClass('is-initialized');

  hideEndFade($scrollingTabs);
  $(window).off('resize.nav').on('resize.nav', () => {
    return hideEndFade($scrollingTabs);
  });
});

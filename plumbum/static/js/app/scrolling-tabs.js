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
    hideEndFade($scrollingTabs);
  });

  $scrollingTabs.off('scroll').on('scroll', (event) => {
    var $this, currentPosition, maxPosition;
    $this = $(event.target);
    currentPosition = $this.scrollLeft();
    maxPosition = $this.prop('scrollWidth') - $this.outerWidth();
    $this.siblings('.fade-left').toggleClass('scrolling', currentPosition > 0);
    $this.siblings('.fade-right').toggleClass('scrolling', currentPosition < maxPosition - 1);
  });

  $scrollingTabs.each((idx, el) => {
    var $this = $(el);
    var scrollingTabWidth = $this.width();
    var $active = $this.find('.active');
    var activeWidth = $active.width();

    if ($active.length) {
      var offset = $active.offset().left + activeWidth;

      if (offset > scrollingTabWidth - 30) {
        var scrollLeft = scrollingTabWidth / 2;
        scrollLeft = (offset - scrollLeft) - (activeWidth / 2);
        $this.scrollLeft(scrollLeft);
      }
    }
  });
});

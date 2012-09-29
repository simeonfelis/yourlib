/*
**	Anderson Ferminiano
**	contato@andersonferminiano.com -- feel free to contact me for bugs or new implementations.
**	jQuery ScrollPagination
**	28th/March/2011
**	http://andersonferminiano.com/jqueryscrollpagination/
**	You may use this script for free, but keep my credits.
**	Thank you.
*/

(function( $ ){
	 
		 
 $.fn.scrollPagination = function(options) {
		var opts = $.extend($.fn.scrollPagination.defaults, options);  
		
		var target = opts.scrollTarget;
		if (target == null){
			target = obj; 
	 	}
		opts.scrollTarget = target;
		
		(this).data("scrollPaginationOptions", opts);
	 
		return this.each(function() {
		  $.fn.scrollPagination.init($(this), opts);
		});

  };
  
  $.fn.scrollPagination.init = function(obj, opts){
     var target = opts.scrollTarget;
     $(obj).attr('scrollPagination', 'enabled');
    
     $(target).scroll(function(event){
         console.log("scroll event");
        if ($(obj).attr('scrollPagination') == 'enabled'){
            $.fn.scrollPagination.loadContent(obj, opts);       
        }
        else {
            event.stopPropagation();    
        }
     });
     
     $.fn.scrollPagination.loadContent(obj, opts);
     
 };
  
  $.fn.stopScrollPagination = function(){
    console.log("stopScrollPagination");
	  return this.each(function() {
	 	$(this).attr('scrollPagination', 'disabled');
	  });
	  
  };
  
  $.fn.scrollPagination.loadContent = function(obj, opts){
      console.log("loadContent");
	 var target = opts.scrollTarget;
	 var scrollTop =  $(target).scrollTop();
	 var docHeight = $(document).height();
	 var targetHeight = $(target).height();
	 var appendTargetHeight = $(opts.appendTarget).height();
	 //var mayLoadContent = $(target).scrollTop()+opts.heightOffset >= $(target).height(); //$(document).height() - $(target).height();
	 var mayLoadContent = $(target).scrollTop() + $(target).height() + opts.heightOffset >= appendTargetHeight;
	 if (mayLoadContent){
		 if (opts.beforeLoad != null){
			opts.beforeLoad(); 
		 }
		 $(obj).children().attr('rel', 'loaded');
		 $.ajax({
			  type: 'POST',
			  url: opts.contentPage,
			  data: opts.contentData,
			  success: function(data){
				$(opts.appendTarget).append(data); 
				var objectsRendered = $(opts.appendTarget).children('[rel!=loaded]');
				
				if (opts.afterLoad != null){
					opts.afterLoad(objectsRendered);	
				}
			  },
			  dataType: 'html'
		 });
	 }
	 
  };
  
 $.fn.scrollPagination.defaults = {
      	 'contentPage' : null,
     	 'contentData' : {},
		 'beforeLoad': null,
		 'afterLoad': null	,
		 'scrollTarget': null,  // the one which shows the scrollbar
		 'appendTarget': null,  // where the loaded data should be appended to
		 'heightOffset': 0		  
 };	
})( jQuery );
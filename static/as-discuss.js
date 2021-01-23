function one_comment(comment) {
  var cdiv = d3.create('div')
      .classed('comment', true);

  // add action items
  var cdiv_actions = cdiv.append('div')
    .classed('caction', true);

  var pin = cdiv_actions.append('img')
      .attr('src', 'static/pin.svg')
      .attr('alt', 'Pin/Unpin this comment');

  // source / render toggle
  var render = cdiv_actions.append('img')
    .attr('src', 'static/code-slash.svg')
    .attr('alt', 'Toggle render / source');

  cdiv_actions.append('a')
    .attr('href', 'discuss?id='+comment.pid+'&cid='+comment._id)
    .append('img')
      .attr('src', 'static/link-45deg.svg')
      .attr('alt', 'Link to this comment');

  // header information: user/time/version
  var cdiv_header = cdiv.append('div')
    .classed('cheader', true)
    .attr('id', '#com' + comment._id);

  cdiv_header.append('div')
    .classed('cuser', true)
    .html('@'+comment.user);

  cdiv_header.append('div')
    .classed('ctime', true)
    .html(timeConverter(comment.time_posted));

  cdiv_header.append('div')
    .classed('cver', true)
    .html('v'+comment.version);

  cdiv_header.append('div')
    .classed('cconf', true)
    .html(comment.conf);

  // actual comment
  var text = '';
  if(typeof comment.text !== 'undefined') {
    var text = comment.text;
  }

  var body = cdiv.append('div')
    .attr('class', 'ctext')
    .attr('id', '#com' + comment._id + 'body')
    .html(marked(text));

  var source = cdiv.append('textarea')
    .classed('source', true)
    .classed('tex2jax_ignore', true)
    .attr('rows', 15)
    .attr('cols', 80)
    .attr('readonly', true)
    .attr('id', '#com' + comment._id + 'source')
    .style('display', 'none')
    .style('resize', 'none')
    .html(text);

  pin.on('click', function(cid){return function(){
    var pin = d3.select(this);
    $.post("/pinmessage", {
      'comment_id': cid
    }).done(function(){
      if(pin.attr('src') == 'static/pin-fill.svg') {
        pin.attr('src', 'static/pin.svg');
      } else {
        pin.attr('src', 'static/pin-fill.svg');
      }
    }).fail(function(jqXHR){
      console.log(jqXHR.responseText);
    });
  }}(comment._id));

  render.on('click', function(body, source){return function(){
    var display = body.style('display');
    body.style('display', source.style('display'));

    var render = d3.select(this);
    source.style('display', display);
    if(render.attr('src') == 'static/journal-text.svg') {
      render.attr('src', 'static/code-slash.svg')
    } else {
      render.attr('src', 'static/journal-text.svg')
    }
  }}(body, source));

  if (typeof MathJax !== 'undefined') {
    MathJax.typeset(body);
  }

  // tags
  var node = cdiv.append('div')
    .classed('ctags', true);

  // now insert tags into tags div
  for(var j = 0; j < tags.length; j++) {
    var tag_count = comment.tags[j];

    var cdiv_tag_count = node.append('div')
      .classed('ctag-count', true)
      .classed('ctag-count-zero', tag_count === 0)
      .html(tag_count);

    var cdiv_tag = node.append('div')
      .classed('ctag', true)
      .html(tags[j]);

    // attach a click handler
    cdiv_tag.on('click', function(tag, count, pid, cid){return function(){
      // inform the server with a POST request
      $.post("/toggletag", {
        'tag_name': tag.html(),
        'comment_id': cid,
        'pid': pid
      }).done(function(){
          // toggle the visual state
          var is_active = !tag.classed('ctag-active');
          tag.classed('ctag-active', is_active);

          // also (de/in)crement the count
          var new_count = parseInt(count.html()) + (is_active ? 1.0 : -1.0);
          if(new_count < 0) { new_count = 0; } // should never happen
          count.html(new_count);

      }).fail(function(jqXHR){
        console.log(jqXHR.responseText);
      });
    }}(cdiv_tag, cdiv_tag_count, comment.pid, comment._id));
  }

  return cdiv;
}


function renderComments() {
  // https://icons.getbootstrap.com/
  var root = d3.select("#discussion");
  if(comments.length > 0) {
    comments.forEach(
      x => root.append(() => one_comment(x).node())
    );
  } else {
    root.append('div')
      .html('none, so far.');
  }
}

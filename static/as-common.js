// various JS utilities shared by all templates

// helper function so that we can access keys in url bar
var QueryString = function () {
  // This function is anonymous, is executed immediately and 
  // the return value is assigned to QueryString!
  var query = {};

  window.location.search.substring(1).split("&").forEach(x => {
    var pair = x.split("=");
    var key = pair[0], val = decodeURIComponent(pair[1]);

    if (typeof query[key] === "undefined") {
      // If first entry with this name
      query[key] = val;
    } else if (typeof query[key] === "string") {
      // If second entry with this name
      query[key] = [query[key], val];
    } else {
      // If third or later entry with this name
      query[key].push(val);
    }
  })

  return query;
}();


function jq( myid ) {
  // for dealing with ids that have . in them
  return myid.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
}


function ocoins_span(paper) {
  // Generate OpenURL COinS metadata element -- readable by Zotero, Mendeley, etc.
  var category = " [" + paper.category.substring(0, paper.category.indexOf('.')) + "]";
  var ocoins_info = {
    "ctx_ver": "Z39.88-2004",
    "rft_val_fmt": "info:ofi/fmt:kev:mtx:journal",
    "rfr_id": "info:sid/arxiv-sanity.com:arxiv-sanity",
    "rft_id": paper.link,
    "rft.atitle": paper.title,
    "rft.jtitle": "arXiv:" + paper.pid + category,
    "rft.date": paper.published_time,
    "rft.artnum": paper.pid,
    "rft.genre": "preprint",

    // NB: Stolen from Dublin Core; Zotero understands
    // this even though it's not part of COinS
    "rft.description": paper.abstract,
  };
  ocoins_info = $.param(ocoins_info);
  ocoins_info += "&" + paper.authors.map(
    x => "rft.au=" + encodeURIComponent(x)
  ).join("&");

  var node = d3.create('span')
    .classed('Z3988', true)
    .attr('title', ocoins_info);

  return node;
}


function one_paper_header(paper) {
  var node = d3.create('div')
    .classed('paperdesc', true);

  // title
  node.append('span')
    .classed('ts', true)
    .append('a')
      .attr('target', '_blank')
      .attr('href', paper.link)
      .html(paper.title);

  // authors
  node.append('br');
  node.append('span')
    .classed('as', true)
    .html(paper.authors.map(
      x => '<a href="/search?q=' + x.replace(/ /g, "+") + '">' + x + '</a>'
    ).join(', '));

  // publication date
  node.append('br');
  node.append('span')
    .classed('ds', true)
    .html(paper.published_time);

  if(paper.originally_published_time !== paper.published_time) {
    node.append('span')
      .classed('ds2', true)
      .html('(v1: ' + paper.originally_published_time + ')');
  }

  // categories and comment
  node.append('span')
    .classed('cs', true)
    .html(paper.tags.map(
      x => '<a href="/search?q=' + x.replace(/ /g, "+") + '">' + x + '</a>'
    ).join(', '));

  node.append('br');
  node.append('span')
    .classed('ccs', true)
    .html(paper.comment);

  return node;
}


function strip_version(pidv) {
  var lst = pidv.split('v');
  return lst[0];
}


function one_paper_actions(paper) {
  // action items for each paper
  var node = d3.create('div')
    .classed('dllinks', true);

  // show raw arxiv id
  node.append('span')
    .classed('spid', true)
    .html(paper.pid);

  // convert from /abs/ link to /pdf/ link. url hacking. slightly naughty
  var pdf_link = paper.link.replace("abs", "pdf");
  if(pdf_link === paper.link) {
    // replace failed, lets fall back on arxiv landing page
    var pdf_url = pdf_link
  } else {
    var pdf_url = pdf_link + '.pdf';
  }

  // access PDF of the paper
  node.append('a')
    .attr('href', pdf_url)
    .attr('target', '_blank')
    .html('pdf');
  
  node.append('br');

  // rank by tfidf similarity
  var similar_span = node.append('span')
    .classed('sim', true)
    .attr('id', 'sim'+paper.pid)
    .html('show similar');

  // attach a click handler to redirect for similarity search
  similar_span.on('click', function(pid){
    return function() { window.location.replace('/' + pid); }
  }(paper.pid)); // closer over the paper id

  // discussion
  var pid = strip_version(paper.pid);
  if (paper.num_discussion > 0) {
    var donwload_span = node.append('span')
      .classed('sim', true)
      .attr('style', 'margin-left:5px; padding-left: 5px; border-left: 1px solid black;')
      .append('a')
        .attr('href', 'export?id=' + pid)
        .attr('target', '_blank')
        .attr('download', pid + '.tex')
        .html('export');
  }

  // var review_span = node.append('span')
  //   .classed('sim', true)
  //   .attr('style', 'margin-left:5px; padding-left: 5px; border-left: 1px solid black;')
  //   .append('a')
  //   .attr('href', 'http://www.shortscience.org/paper?bibtexKey='+paper.pid)
  //   .html('review');

  var discuss_text = paper.num_discussion === 0 ? 'discuss' : 'discuss [' + paper.num_discussion + ']';
  var discuss_color = paper.num_discussion === 0 ? 'black' : 'red';
  var review_span = node.append('span')
    .classed('sim', true)
    .attr('style', 'margin-left:5px; padding-left: 5px; border-left: 1px solid black;')
    .append('a')
      .attr('href', 'discuss?id=' + pid)
      .attr('style', 'color:' + discuss_color)
      .html(discuss_text);

  node.append('br');

  var lib_state_img = paper.in_library === 1 ? 'static/saved.png' : 'static/save.png';
  var saveimg = node.append('img')
    .attr('src', lib_state_img)
    .classed('save-icon', true)
    .attr('title', 'toggle save paper to library (requires login)')
    .attr('id', 'lib'+paper.pid);

  // attach a handler for in-library toggle
  saveimg.on('click', function(pid, elt){
    return function() {
      if(username !== '') {
        // issue the post request to the server
        $.post("/libtoggle", {
          pid: pid
        }).done(function(data){
          // toggle state of the image to reflect the state of the server, as reported by response
          if(data === 'ON') {
            elt.attr('src', 'static/saved.png');
          } else if(data === 'OFF') {
            elt.attr('src', 'static/save.png');
          }
        });
      } else {
        alert('you must be logged in to save papers to library.')
      }
    }
  }(paper.pid, saveimg)); // close over the pid and handle to the image

  return node;
}

function one_paper(paper) {
  var node = d3.create('div')
    .classed('apaper', true)
    .attr('id', paper.pid);

  // OpenURL COinS metadata
  node.append(() => ocoins_span(paper).node());

  // title and acgtions
  node.append(() => one_paper_header(paper).node());
  node.append(() => one_paper_actions(paper).node());

  // separator
  node.append('div')
    .attr('style', 'clear:both');

  // thumbnail
  if(typeof paper.img !== 'undefined') {
    node.append('div')
      .classed('animg', true)
      .append('img')
        .attr('onerror', "this.onerror=null; this.src='static/missing.jpg'")
        .attr('src', paper.img);
  }

  // abstract
  if(typeof paper.abstract !== 'undefined') {
    var abdiv = node.append('span')
      .classed('tt', true)
      .html(paper.abstract);

    //typeset the added paper
    MathJax.typeset(abdiv);
  }

  return node;
}

function one_tweet_highlight(elt, tweet, imgelt){
  // mouseover handler: show tweet text and highlight user pic.
  return function() {
    // make visible and clear it
    elt.attr('style', 'display:block;')
      .html('');

    // show tweet source
    elt.append('div')
      .append('a')
        .attr('href', 'https://twitter.com/' + tweet.screen_name + '/status/' + tweet.id)
        .attr('target', '_blank')
        .attr('style', 'font-weight:bold; color:#05f; text-decoration:none;')
        .text('@' + tweet.screen_name + ':');

    // show tweet text
    elt.append('div')
      .text(tweet.text)

    imgelt.attr('style', 'border: 2px solid #05f;'); 
  }
}

function one_paper_show_tweets(collection) {
  var node = d3.create('div');

  var tdiv = node.append('div')
    .classed('twdiv', true);

  tdiv.append('div')
    .classed('tweetcount', true)
    .text(collection.num_tweets + ' tweets:');

  var tcontentdiv = node.append('div')
    .classed('twcont', true);

  var tweets = collection[ix].tweets;

  tweets.forEach(function(tweet) {
    // distinguish non-boring tweets visually making their border green
    var border_col = tweet.ok ? '#3c3' : '#fff';

    var timgdiv = tdiv.append('img')
      .classed('twimg', true)
      .attr('src', tweet.image_url)
      .attr('style', 'border: 2px solid ' + border_col + ';');

    var highight = one_tweet_highlight(tcontentdiv, tweet, timgdiv);
    timgdiv.on('mouseover', highight)
      .on('click', highight)
      .on('mouseout', function(elt, col) {
        return function() {
          elt.attr('style', 'border: 2px solid ' + col + ';');
        }}(timgdiv, border_col)
      );
  });

  return node;
}

function timeConverter(UNIX_timestamp){
  var a = new Date(UNIX_timestamp * 1000);
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var year = a.getFullYear();
  var month = months[a.getMonth()];
  var date = a.getDate().toString();
  var hour = a.getHours().toString();
  var min = a.getMinutes().toString();
  var sec = a.getSeconds().toString();
  if(hour.length === 1) { hour = '0' + hour; }
  if(min.length === 1) { min = '0' + min; }
  if(sec.length === 1) { sec = '0' + sec; }
  var time = date + ' ' + month + ' ' + year + ', ' + hour + ':' + min + ':' + sec ;
  return time;
}

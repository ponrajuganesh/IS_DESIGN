$(document).ready(function() {

  var products_string = $('#products_string').val().trim();
  var sold_count_string = $('#sold_count_string').val().trim();

  console.log(products_string);
  console.log(sold_count_string);

  var products = products_string.split(",");
  products.unshift('Products');

  var counts = sold_count_string.split(",");
  counts.unshift('Counts')

  var data = {}
  data['x'] = 'Products';
  data['type'] = 'bar';
  data['columns'] = [];
  data['columns'].push(products);
  data['columns'].push(counts);

  var axis = {};
  axis['x'] = {};
  axis['x']['type'] = 'category';

  var graph_data = {};
  graph_data["data"] = data;
  graph_data["axis"] = axis;

  console.log(JSON.stringify(graph_data));

  var chart = c3.generate({
    bindto: '#chart',
    data: data,
    axis: axis
  });

})

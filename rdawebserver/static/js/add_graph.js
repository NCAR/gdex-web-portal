function add_graph(dsid){
    d3.select('#content_container').append('div').attr('id', 'graph').style('height', '500px');
    console.log('here');
    container = document.getElementById('graph');
    myGraph = new MetricsGraph(container, '/media/metrics/aliases.json');
    myGraph.addData('/media/metrics/year/'+dsid+'metrics.json', dsid);
    d3.select('#month').on('click', function(){
        myGraph.removeAllData();
        myGraph.addData('/media/metrics/month/'+dsid+'metrics.json', dsid);
        d3.select('#month').style('color', '#333');
        d3.select('#year').style('color', '#aaa');
        });
    d3.select('#year').on('click', function(){
        myGraph.removeAllData();
        myGraph.addData('/media/metrics/year/'+dsid+'metrics.json', dsid);
        d3.select('#month').style('color', '#aaa');
        d3.select('#year').style('color', '#333');
        });
}

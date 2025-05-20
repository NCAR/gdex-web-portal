/*
 * MetricsGraph Class
 * ------------------
 * Initializes metrics graph.
 *
 * After initialization, data can be added via the addData() function.
 * Note: For best results, container should be empty.
 */
function MetricsGraph(container, aliasesFile, config)
{
    this.container = container;
    this.computeSize(container); // Get screen dimensions
    this.initConfig();
    this.initGraph(container); // Only called once; creates graph skeleton
    this.data = [];
    this.dataObjs = [];

    curkey = undefined;

    // Optionally provide an aliases file
    // that maps from key given in json to a different key name.
    this.aliasesFile = aliasesFile;
    this.numData = 0;
}
/**
 *  Initializes object level configuration which modifies functionality.
 */
MetricsGraph.prototype.initConfig = function()
{
    this.config = {
        'initialKey' : undefined,
        'graph' : {
            'type' : 'bar', // 'bar' or 'line'
            'zeroMinRange' : false, // Scale to data range
            'transEase' : d3.easeQuad, // type of transition. More eases found https://github.com/d3/d3-ease
            'baselineMaxRange' : {}
        },
        'time' : {
            // Extra space on x axis.
            'minBuffer' : 5, // Units of percent
            'maxBuffer' : 5,  // Units of percent
            'onlyMonth' : false // only use the month in the date string
        },
        'bars' : {
            'width' : () => {return (this.width * .045) ; }//was 35px}
        },
        'color' : d3.scaleOrdinal(d3.schemeCategory10).domain(20)
    };
}
/**
 *  Draws a small line in given container.
 *
 *  This is used for changing graph types.
 */
function drawMiniLine(container)
{
    container
        .append('path')
        .attr('id', 'miniLine')
        .attr('d', "M 5 10 C 8 35, 9 3, 13 21 S 28 1, 25 10")
        .style('fill', 'none')
        .style('stroke-width', '2px')
        .style('stroke', 'green');
}
/**
 *  Draws a small set of bars in given container.
 *
 *  This is used for changing graph types.
 */
function drawMiniBar(container)
{
    var miniG = container.append('g')
        .attr('id', 'miniBar');
    for(var i=0; i<3; i++)
    {
        miniG
            .append('rect')
            .attr('height',5+(i*8))
            .attr('width','5')
            .attr('x', 4+(i*8))
            .attr('y', 22 - (i*8))
            .style('fill', 'blue')
    }
}
/**
 *  Draws small bar/lines in top right of screen, and handles when clicked
 *
 *  This is used for changing graph types. When changed to either line/bar,
 *  it changes the config.graph.type and calls reDraw()
 */
MetricsGraph.prototype.drawConfig = function(container)
{
    var configWidth = 30;
    var configHeight = 30;
    var configContainer = container.append('g')
        .attr('id', 'config')
        .attr('transform', 'translate('+(this.width - (configWidth) - this.margin.right -this.margin.left )+','+(-this.margin.top)+')')
    configContainer
        .append('rect')
        .attr('width', configWidth)
        .attr('height', configHeight)
        .attr('rx', '5')
        .style('fill', 'white')
        .style('stroke', 'gray')
        .style('stroke-width', '1px')
    if(this.config.graph.type == 'bar')
    {
        drawMiniLine(configContainer)
    }
    configContainer.on('click', () => {
        this.reDraw(configContainer)
    }
    );
}
MetricsGraph.prototype.addBaseline = function(json)
{
    d3.selectAll('.baseline').remove();
    if(curkey in this.config.graph.baselineMaxRange)
    {
        myGraph.svg.append('line')
            .attr('id', 'baselineline')
            .attr('x1', 0)
            .attr('x2', this.width - this.margin.left - this.margin.right)
            .attr('y1', this.y(this.config.graph.baselineMaxRange[curkey]))
            .attr('y2', this.y(this.config.graph.baselineMaxRange[curkey]))
            .style('stroke', '#000')
            .style('stroke-width', '2px')
            .style('stroke-dasharray', '5,5')
            .classed('baseline', true)

        myGraph.svg.append('text')
        .attr('x', (this.width - this.margin.left - this.margin.right)/2)
        .attr('y', this.y(this.config.graph.baselineMaxRange[curkey])-5)
        .classed('baseline', true)
        .text('max');
    }
}
/**
 * Removes and saves data, then adds it back into the graph.
 * Adds the data back in with a delay to prevent race conditions.
 * Useful if changing configuration.
 */
MetricsGraph.prototype.reDraw = function(configContainer)
{
    tmpName = [];
    tmpJson = []
    for(i in this.dataObjs)
    {
        cur = this.dataObjs[i]
        tmpName.push(cur.name);
        tmpJson.push(cur.jsonFile);
    }
    for(i in tmpName)
    {
        this.removeData(tmpName[i]);
    }
    if(configContainer !== undefined)
    {
        if(this.config.graph.type == 'bar')
        {
            curkey = 'Number of Files Read';
            this.config.graph.type = 'line';
            d3.select('#miniLine').remove();
            drawMiniBar(configContainer)
        }
        else
        {
            this.config.graph.type = 'bar';
            d3.select('#miniBar').remove()
            drawMiniLine(configContainer)
        }
    }
    // Need to offset when the data is added back into the graph
    // since they would be drawn as the same color.
    for(i in tmpName)
    {
        (() => {
            var _i = i;
            offset = _i*400;
            setTimeout(() => {this.addData(tmpJson[_i],tmpName[_i])}, offset)
        })();
    }
}
/**
 * Removes all data from graph.
 *
 * Additionally updates the graph parameters and removes key.
 */
MetricsGraph.prototype.removeAllData = function()
{
    removeSortByMenu();
    d3.selectAll('.multBars').remove()
    while(this.dataObjs.length > 0)
    {
        cur = this.dataObjs.pop();
        if (this.config.graph.type == 'line')
        {
            cur.line.remove();
            cur.dots.remove();
        }
        else
        {
            try
            {
                cur.bars.remove()
            }
            catch {}
        }
        cur.infoBox.element.remove();

        this.numData--;
        this.dataObjs.splice(i,1);
        this.data.pop();

        //update graph
        this.updateGraphParams();
        this.updateLines();
        this.drawKey();

    }
}
/**
 * Removes one dataset given by the title of the dataset.
 */
MetricsGraph.prototype.removeData = function(title)
{
    // Iterate through data objects until title is found
    for(i in this.dataObjs)
    {
        cur = this.dataObjs[i];
        if(cur.name == title)
        {
            if(this.config.graph.type == 'line')
            {
                cur.line.remove();
                cur.dots.remove();
            }
            else if(this.config.graph.type == 'bar')
            {
                if(cur.bars === undefined)
                    d3.selectAll('.multBars').remove()
                else
                    cur.bars.remove();
            }
            cur.infoBox.element.remove();

            this.numData--;
            this.dataObjs.splice(i,1);
            this.data.splice(i,1);

            //update graph
            this.updateGraphParams();
            this.updateLines();
            this.drawKey();

            removeSortByMenu();
            if(this.dataObjs.length != 0)
            {
                this.drawTopicSelector();
            }
            // Case when graph is empty
            if(this.dataObjs.length == 0)
            {
                this.units = undefined;
            }
            return title;
        }
    }
}
/**
 * Adds data to the current graph, updates graph, and displays bars/lines.
 */
MetricsGraph.prototype.addData = function(jsonFile, title)
{
    // Give title if not provided
    if(title === undefined)
        title = jsonFile;
    d3.select(this.container).select('#source_link').remove()
    d3.select(this.container).append('a')
        .attr('href', jsonFile)
        .attr('id', 'source_link')
        .text('Source JSON')
    //this.curColor = this.config.color(this.dataObjs.length);
    this.curColor = this.config.color(this.numData);
    this.numData++;
    // Read json, then execute callback
    d3.json(jsonFile).then( (data) =>
        {
            // Attempt to massage data into more usable format
            data = this.initData(data);
            this.data.push(data);
            // Make this a method
            if(curkey === undefined &&
                this.config.initialKey !== undefined &&
                this.all_keys.includes(this.config.initialKey))
            {
                curkey = this.config.initialKey;
            }
            else if(curkey !== undefined && this.all_keys.includes(curkey))
            {

            }
            else
            {
                curkey = this.all_keys[0];
            }

            this.updateGraphParams();
            var line = null;
            var dots = null;
            var bars = null;
            if(this.config.graph.type == 'line')
            {
                var line = this.drawLine(data);
                var dots = this.drawDots(data);
            }
            else if(this.config.graph.type == 'bar')
            {
                var bars = this.drawBars(data);
            }
            var infoBox = this.createInfoBox();
            dataObj = {
                'jsonFile' : jsonFile,
                'data' : data,
                'name' : title,
                'line' : line,
                'dots' : dots,
                'bars' : bars,
                'color' : this.curColor,
                'infoBox' : {
                    'element' : infoBox,
                    'cx' : 0,
                    'cy' : 0
                }
            }
            this.dataObjs.push(dataObj);
            this.updateLines();
            this.addBaseline();
            removeSortByMenu();
            this.drawTopicSelector();
            this.drawTitle();
        });
}
/**
 * Given data, converts to just month view if wanted in config
 */
MetricsGraph.prototype.convertDate = function(data)
{
    // Converts date string if needed
    if(this.config.time.onlyMonth)
    {
        for(i in data)
        {
            date = data[i].Date;
            if(date.length == 7) // assume YYYY-mm
            {
                date = date.slice(5,7)
                data[i].Date = date
            }
        }
    }
    return data;
}
/**
 * Given Data, converts value to 'Date' key to js Date object
 */
MetricsGraph.prototype.convertTimeStr = function(data)
{
    // Given data is array of objects with 'Date' as a key
    var parseDateMonthAlt = d3.timeParse("%m");
    var parseDateMonth = d3.timeParse("%Y-%m");
    var parseDateDay = d3.timeParse("%Y-%m-%d");
    var parseDateHour = d3.timeParse("%Y-%m-%d %H:%M");
    var parseYear = d3.timeParse("%Y");
    for(i in data)
    {
        if(data[i].Date.length == 16)
            data[i].Date = parseDateHour(data[i].Date);
        else if(data[i].Date.length == 10)
            data[i].Date = parseDateDay(data[i].Date);
        else if(data[i].Date.length == 7)
            data[i].Date = parseDateMonth(data[i].Date);
        else if(data[i].Date.length == 4)
            data[i].Date = parseYear(data[i].Date);
        else if(data[i].Date.length == 2)
            data[i].Date = parseDateMonthAlt(data[i].Date);
    }
    return data;
}
/**
 * Given data, converts data to be more usable
 * dict to array.
 * e.g. From:
 * {'key':{...}, 'key':{...}}
 * to
 * [{...},{...}]
 */
MetricsGraph.prototype.initData = function(data)
{
    data = convertToArray(data);
    data = this.convertDate(data);
    data = this.convertTimeStr(data);
    if(this.units === undefined)
    {
        out = convertDataSize(data);
        data = out[0];
        this.units = out[1];
    }
    else
    {
        data = convertDataSize(data, this.units)[0];
    }

    this.all_keys = Object.keys(data[0]);
    popElement(this.all_keys, 'Date')

    return data;
}
/**
 * Draws the sort-by menu
 */
MetricsGraph.prototype.drawTopicSelector = function()
{
    var curObj = this;
    var temp_keys = this.all_keys.slice(0); // clone
    temp_keys.sort();
    popElement(temp_keys, 'Date')
    if(this.aliasesFile === undefined)
    {
        drawSortByMenu(this.svg,temp_keys, 0,-this.margin.top,
            // Callback function
            function() {
                var new_curkey = d3.select(this).attr('data');
                if(new_curkey != curkey)
                {
                    curkey = new_curkey;
                    curObj.updateGraphParams();
                    curObj.addBaseline();
                    curObj.updateLines();
                    curObj.drawTitle();
                }
            });
    }
    else // If there are aliases
    {
        d3.json(this.aliasesFile).then( (data) =>
            {
                // Convert keys aliases
                invertedData = {}
                for(i in temp_keys)
                {
                    key = temp_keys[i];
                    if(key in data)
                    {
                        invertedData[data[key]] = temp_keys[i]
                        temp_keys[i] = data[key]
                    }
                }
                // Can't draw multBars with more than one dataset
                if( this.dataObjs.length > 1)
                {
                    popMethods(temp_keys, 'Method');
                }
                // Don't draw totals with only one dataset
                if( this.dataObjs.length == 1)
                {
                    popMethods(temp_keys, 'Total');
                }

                drawSortByMenu(this.svg,temp_keys, 10,-this.margin.top,
                    // Callback function
                    function(){
                        d3.selectAll('.infoBox').style('visibility', 'hidden')
                        selectedKey = d3.select(this).attr('data');
                        new_curkey = invertedData[selectedKey] || selectedKey;
                        if(new_curkey != curkey)
                        {
                            curkey = new_curkey;
                            curObj.updateGraphParams();
                            curObj.updateLines();
                            curObj.drawTitle();
                        }
                    });
            });
    }
}
/**
 * Remove keys that have include ```matchStr```
 */
function popMethods(keys, matchStr)
{
    keys_copy = keys.slice();
    for(i in keys_copy)
    {
        tmp_key = keys_copy[i]
        if(tmp_key.includes(matchStr))
        {
            popElement(keys, tmp_key)
        }
    }
}
/**
 * Given [min, max], Decrease min and increase max 'percent' amount
 *
 * e.g. increaseRange([10,100], 10) yeilds [1,109]
 */
function increaseRange(arr, percent)
{
    range = arr[1] - arr[0];
    buffer = range*(percent/100);
    var minWithBuffer = arr[0] - buffer
    var maxWithBuffer = arr[1] + buffer
    if(minWithBuffer <= 0)
        minWithBuffer = 0;
    return [minWithBuffer, maxWithBuffer];
}
/**
 * Sets the the domain of the axes.
 *
 * Domain information is accessed via
 * this.y.domain and this.x.domain
 */
MetricsGraph.prototype.setDomain = function()
{
    // Find minimum y value
    var ymin = 0;
    if( ! this.config.graph.zeroMinRange) // scale to data range
    {
        ymin = d3.min(this.data, function(d) {
            return d3.min(d, function(l) {
                if(typeof(l[curkey]) == "object")
                    return d3.min(Object.values(l[curkey]));
                else
                    return l[curkey];
            })
        });
    }
    // scale to data range
    var ymax = 0;
    if(curkey in this.config.graph.baselineMaxRange)
    {
        ymax = this.config.graph.baselineMaxRange[curkey]
        // Add buffer
        ymax = ymax + ((ymax - ymin)*.05)
    }
    else
        ymax = d3.max(this.data, function(d) {
            return d3.max(d, function(l) {
                    if(typeof(l[curkey]) == "object")
                        return d3.sum(Object.values(l[curkey]));
                    else
                        return l[curkey];
                })
        });
    // Set min and max value for x axis.
    // Currently assumes that 'Date' is available in d.
    // Adds additional buffer so datapoint doesn't start on y axis
    var xmin = d3.min(this.data, (d) => {
        var min = d3.min(d, function(l){return l.Date})
        return min
    });
    var xmax = d3.max(this.data, (d) => {
        var max = d3.max(d, function(l){return l.Date})
        return max
    });
    // Make buffer minBuffer % of time difference
    numDays = getDurationInDays(new Date(xmin), new Date(xmax));
    minBuffer = Math.floor(numDays * (this.config.time.minBuffer/100));
    maxBuffer = Math.floor(numDays * (this.config.time.maxBuffer/100));
    var xmin = new Date(String(xmin));
    var xmax = new Date(String(xmax));
    console.log(numDays)
    if(numDays < 2)
    {
        xmin = xmin.setHours(xmin.getHours()-1)
        xmax = xmax.setHours(xmax.getHours()+1)
    }
    else
    {
        xmin = xmin.setDate(xmin.getDate()-minBuffer)
        xmax = xmax.setDate(xmax.getDate()+maxBuffer)
    }

    xRange = [xmin,xmax];
    yRange = [ymin,ymax];

    // Give a little leeyway for domain/range
    yRange = increaseRange(yRange, 5);

    this.y.domain(yRange);
    this.x.domain(xRange);

}

/**
 * Given start and end date in miliseconds, get difference in days.
 */
function getDurationInDays(startDate, endDate)
{
    var numMiliseconds = endDate - startDate;
    var deltaDays = numMiliseconds / 1000 / 60 / 60 / 24;
    return deltaDays;
}
MetricsGraph.prototype.changeKey = function(key)
{
    curkey = key;
}
MetricsGraph.prototype.updateGraphParams = function()
{
    this.setDomain();
    this.drawAxes();
}
MetricsGraph.prototype.updateLines = function()
{
    for(i in this.dataObjs)
    {
        cur = this.dataObjs[i];
        if(this.config.graph.type == 'line')
        {
            this.drawLine(cur.data, cur.line);
            this.drawDots(cur.data, cur.dots);
            this.drawKey();
        }
        else if(this.config.graph.type == 'bar')
        {
            cur.bars = this.drawBars(cur.data, cur.bars, i)
        }

    }
}
MetricsGraph.prototype.drawDots = function(data, dots)
{
    if(typeof data[0][curkey] == "object")
    {
        dots = this.drawDotsMult(data, dots);
        return dots;
    }
    if(dots === undefined)
    {
        dots = this.svg.selectAll(".nothing") //selection shouldn't exist
            .data(data)
            .enter().append("circle")
            .attr("class", "dot") // Assign a class for styling
            .attr("cx", (d, i) => { return this.x(d.Date) })
            .attr("cy", (d) => { return this.y(d[curkey]) })
            .attr("r", 4)
            .style('fill', this.curColor);
    }
    else
    {
        dots.transition()
            .attr("cx", (d, i) => { return this.x(d.Date) })
            .attr("cy", (d) => { return this.y(d[curkey]) })
    }
    return dots;
}
/**
 *
 */
MetricsGraph.prototype.drawBars = function(data, bar, pos)
{
    // pos is to keep track of which bar should be drawn first
    var useCurColor = false;
    if(typeof(pos) === typeof(undefined))
    {
        pos = 0;
        useCurColor = true;
    }
    if(this.dataObjs.length == 0)
        var numData = 1;
    else
        var numData = this.dataObjs.length;
    if(typeof data[0][curkey] == "object")
    {
        //d3.selectAll('.multBars').remove()
        if(this.dataObjs.length > 0) //&& this.dataObjs[0].bars !== undefined)
        {
            tmpBars = this.dataObjs[0].bars;
            if(tmpBars.isMult)
                tmpBars = tmpBars.selectAll('rect')
            tmpBars
                .transition()
                .duration(500)
                .ease(this.config.graph.transEase)
                .attr('height', 0)
                .attr('y', (d) => {return this.y(0)})
                .on('end', function (){
                    d3.select(this)
                        .remove()
                });
        }
        bar = this.drawBarsMult(data, bar);
        return bar;
    }
    this.drawKey();
    if(bar === undefined || bar.isMult) // Either first draw, or multBars exist
    {
        d3.selectAll('.multBars').remove()
        bar = this.svg.select('#dataEles')
            .selectAll(".nothing") //selection shouldn't exist
            .data(data)
            .enter().append("rect")
            .attr("class", "bar") // Assign a class for styling
            .attr("x", (d, i) => {
                var frac = pos/(numData);
                var retval = this.x(d.Date) -
                    ((this.config.bars.width() / 2) -(pos*this.config.bars.width()) / (numData));

                return retval })
            // Start bar at 0 so it can grow upward.
            .attr('y', (d) => { return this.y(this.y.domain()[0]);})
            .attr("height", (d) => { return 0; })
            .attr("width",(d) => {
                return  this.config.bars.width() / (numData);
            })
            //.style('fill', this.curColor);
            .style('fill',() =>{ return useCurColor ? this.curColor : this.config.color(pos)});
        bar.transition()
            .ease(this.config.graph.transEase)
            .duration(750)
            .attr('y', (d) => { return this.y(d[curkey])})
            .attr("height", (d) => { return (this.y.range()[0] - this.y(d[curkey])) })
    }
    else
    {
        bar.transition()
            .ease(this.config.graph.transEase)
            .duration(750)
            .attr("x", (d, i) => {
                var frac = pos/(numData)
                var retval = this.x(d.Date) -
                    ((this.config.bars.width() / 2) -(pos*this.config.bars.width()) / (numData));

                return retval })
            .attr('y', (d) => { return this.y(d[curkey])})
            .attr("width",(d) => {
                return  this.config.bars.width() / (numData)
            })
            .attr("height", (d) => { return (this.y.range()[0] - this.y(d[curkey])) })
    }
    bar.__proto__.isMult = false;
    return bar;
}
MetricsGraph.prototype.drawLine = function(data, line)
{
    if(typeof(data[0][curkey]) == "object")
    {
        this.drawLineMult(data,line);
        return line
    }

    if(line === undefined) // Create line if not given
    {
        var line = this.svg.append('path')
            .style('stroke', this.curColor)
            .style('stroke-width', '2px')
            .style('fill', 'none')
            .attr('class', 'line')
    }
    line.datum(data)
        .transition()
        .attr('d', this.line);
    return line;
}
MetricsGraph.prototype.drawLineMult = function(data, line)
{
}

/**
* Draws a stacked bar graph.
*/
MetricsGraph.prototype.drawBarsMult = function(data, bars)
{
    console.log('drawing stacked bar graph');
    var tmpx = this.x;
    var tmpy = this.y;
    var tmpcolor = this.curColor;
    var colors = this.config.color;
    var curWidth = this.config.bars.width();
    var colorDict = {};
    var nextColor = 0;
    objectKeys = {};
    bars = d3.select('#dataEles').selectAll(".nothing") //selection shouldn't exist
        .data(data)
        .enter().append("g")
        .attr("class", "multBars") // Assign a class for styling
        .each(function(d,i){
            var delay=-500;
            var curYValue = 0;
            var curYValue2 = 0;
            newData = convertToArrayWithKey(d[curkey]);
            var newDataSum = d3.sum(newData, function(d){return Object.values(d)})
            var tmpData = [];
            // Remove data if it's below a threshold.
            var fractionToRemove = .01;
            var limit = newDataSum * fractionToRemove;
            for(k in newData)
            {
                if(Object.values(newData[k])[0] > limit)
                {
                    tmpData.push(newData[k])
                }
            }
            newData = tmpData;
            // Sort by key name
            newData.sort(function(a,b){return Object.keys(b)[0].charCodeAt(0) - Object.keys(a)[0].charCodeAt(0)});
            // Need to associate objectKeys with a unique color
            d3.select(this)
                .selectAll('.nothing')
                .data(newData)
                .enter()
                .append('rect')
                .classed('multiRect',true)
                .attr('width', curWidth)
                .attr('height',(m,i) => { return 0;(tmpy.range()[0] - tmpy(Object.values(m)[0]))})
                .style('fill', (m,i) => {
                    var name = Object.keys(m)[0];
                    if(name in colorDict)
                        return colorDict[name]
                    else
                    {
                        colorDict[name] = colors(nextColor);
                        nextColor++;
                    }
                    return colorDict[name]
                })
                .attr("x", () => {return (tmpx(d.Date) - curWidth/2)  })
                .attr("y", (m,i) => {
                    var tmpval = curYValue2;
                    //curYValue2 += Object.values(m)[0]; return tmpy(tmpval)
                    return tmpy(0)
                })
                .transition()
                .delay(0)
                .duration(1000)
            //.delay(function() {delay+=250; return delay }) //adds to end of last ele
                .attr("y", (m) => {
                    curYValue += Object.values(m)[0]; return tmpy(curYValue)
                })
                .attr('height',(m,i) => { return (tmpy.range()[0] - tmpy(Object.values(m)[0]))})
                .on('end', function(d)
                    {
                        // Draw Values
                        var thisRect = d3.select(this);
                        if(thisRect.attr('height') > 30 &&  curWidth > 50)
                        {
                            var parentG = d3.select(this.parentNode);
                            var position = thisRect.attr('y')
                            var xpos = parseFloat(thisRect.attr('x')) + parseFloat((curWidth /2))
                            var ypos = parseFloat(thisRect.attr('y'))+18

                            var rectText = parentG.append('text')
                                .attr('y', ypos )
                                .attr('x', xpos)
                                .style('text-anchor', 'middle')
                                .style('fill', 'white');

                            var formatFloat = d3.format(".2f");
                            formatInt = d3.format(",d");
                            var value =  Object.values(d)[0]
                            if(isInt(value))
                                rectText.text(formatInt(value));
                            else
                                rectText.text(formatFloat(value));
                        }

                    })
        })

    // Draw Key
    var entryWidth = 150;
    var curOffset = 0;
    var squareOffset = 15; // offset between color square and text
    var squareLength = 10;
    var container =  d3.select('#keyContainer');
    container.selectAll('g').remove();
    for(i in colorDict)
    {
        var curColor = colorDict[i];
        var keyEntry = container.append('g')
            .attr('transform', 'translate('+curOffset+',-10)');
        keyEntry.append('rect')
            .attr('width', squareLength)
            .attr('height', squareLength)
            .attr('y', -squareLength)
            .style('fill', curColor);
        keyEntry.append('text')
            .attr('x', squareOffset)
            .classed('keytext', true)
            .text(i);
        entryWidth = keyEntry.node().getBBox().width;

        curOffset += (entryWidth + 12);

    }
    bars.__proto__.isMult = true;
    return bars;
}
MetricsGraph.prototype.drawDotsMult = function(data, dots)
{
    var tmpx = this.x;
    var tmpy = this.y;
    var tmpcolor = this.curColor;
    dots = this.svg.selectAll(".nothing") //selection shouldn't exist
        .data(data)
        .enter().append("g")
        .attr("class", "GroupDot") // Assign a class for styling
        .each(function(d,i){
            var delay=-500;
            var curYValue = 0;
            var curYValue2 = 0;
            newData = convertToArrayWithKey(d[curkey]);
            d3.select(this)
                .selectAll('.nothing')
                .data(newData)
                .enter()
                .append('circle')
                .attr('r','5px')
                .style('fill', tmpcolor)
                .attr("cx", function(){return tmpx(d.Date) })
                .attr("cy", (m,i) => { if(i!=0) curYValue2 += Object.values(m)[0];return tmpy(curYValue2)})
                .transition()
                .duration(1000)
                .delay(function() {delay+=500; return delay })
                .attr("cy", (m) => { curYValue += Object.values(m)[0]; return tmpy(curYValue) })
            //.attr('r','5px')
        })
    /*
       .attr("cx", (d, i) => { return this.x(d.Date) })
       .attr("cy", (d) => { return this.y(d[curkey]) })
       .attr("r", 4)
//.style('stroke', 'pink')
//.style('stroke-width', '1px')
    .style('fill', this.curColor);
    */
}

MetricsGraph.prototype.drawKey = function()
{
    var entryWidth = 150;
    var curOffset = 0;
    var squareOffset = 15; // offset between color square and text
    var squareLength = 10;
    var container =  d3.select('#keyContainer');
    container.selectAll('g').remove();
    for(i in this.dataObjs)
    {
        var cur = this.dataObjs[i];
        var keyEntry = container.append('g')
            .attr('transform', 'translate('+curOffset+',-10)');
        keyEntry.append('rect')
            .attr('width', squareLength)
            .attr('height', squareLength)
            .attr('y', -squareLength)
            .style('fill', cur.color);
        keyEntry.append('text')
            .attr('x', squareOffset)
            .classed('keytext', true)
            .text(cur.name);
        entryWidth = keyEntry.node().getBBox().width;

        curOffset += (entryWidth + 12);

    }
}

//
// init
//
MetricsGraph.prototype.drawAxes = function()
{
    this.removeAxes();

    // Draw the X Axis
    var tmpAxes = d3.select('#axes').append('g')
        .attr('id','xAxis')
        .style('font-size', '.85em') // TODO: possibly will want to make this scale by screen width
        .attr("transform", "translate(0," + (this.height - this.margin.bottom - this.margin.top) + ")");

    if(((xRange[1] -xRange[0]) /1000/60/60/24) < 3)
        tmpAxes.call(d3.axisBottom(this.x)
            .tickFormat(d3.timeFormat('%x %H:00')
            ));
    else if(((xRange[1] -xRange[0]) /1000/60/60/24) < 400)
        tmpAxes.call(d3.axisBottom(this.x)
            .tickFormat(d3.timeFormat('%B')
            ));
    else
        tmpAxes.call(d3.axisBottom(this.x))


    // Draw the Y Axis
    d3.select('#axes').append("g")
        .attr('id','yAxis')
        .call(d3.axisLeft(this.y));
    // Draw ticks that go across graph to easier see where values lie.
    var tickGroup = d3.select('#yAxis')
        .selectAll('.tick');
    tickGroup.select('line')
        .attr('x2', (this.width - this.margin.right - this.margin.left))
        .style('opacity', '.1');
    tickGroup.select('text')
        .style('font-size', '1.1em');
}
MetricsGraph.prototype.removeAxes = function()
{
    d3.select('#xAxis').remove();
    d3.select('#yAxis').remove();
}
MetricsGraph.prototype.resetGraph = function()
{
    this.removeAxes();
    d3.select('#title').remove();
    //    d3.selectAll('.dot').remove();
}
/**
 * Draw the current key above graph.
 */
MetricsGraph.prototype.drawTitle = function()
{
    d3.select('#title').remove();
    this.svg.append('text')
        .attr('x', (this.width/2) - this.margin.right)
        .attr('y', '0px')
        .style('text-anchor', 'middle')
        .style('font-size', '1.5em')
        .attr('id', 'title')
        .text(curkey);

}
/**
 * Create an infobox, which will be bound to a dataset
 */
MetricsGraph.prototype.createInfoBox = function()
{
    var infoBox = this.svg.append('g')
        .classed('infoBox', true)
        .style('visibility', 'hidden');
    var rectWidth = 50;
    var rectHeight = 20;
    infoBox.append('rect')
        .style('fill', this.curColor)
        .attr('width', rectWidth)
        .attr('height', rectHeight)
        .attr('x', -rectWidth/2)
        .attr('y', -rectHeight)
        .attr('rx', 4) // Curved edges
        .attr('ry', 4);// Curved edges
    infoBox.append('text')
        .classed('infoBoxText', true)
        .attr('y', -5)
        .style('fill', 'white')
        .style('text-anchor', 'middle');

    return infoBox;
}
/**
 * Draws graph skeleton, inits scales, and other one-time functions
 */
MetricsGraph.prototype.initGraph = function(container)
{
    this.placeSVG(container);
    this.drawConfig(this.svg);
    initDefs(this.svg);

    this.svg.append('g').attr('id', 'axes');
    this.svg.append('g').attr('id', 'dataEles');

    this.x = d3.scaleTime()
        .range([0, this.width - this.margin.left - this.margin.right]); // Account for margin
    this.y = d3.scaleLinear()
        .range([this.height - this.margin.bottom - this.margin.top, 0]);// Account for margin

    xAxis = d3.axisBottom(this.x);
    xAxis.tickSizeOuter(15);
    xAxis.tickFormat(d3.timeFormat("%m"));
    var yAxis = d3.axisLeft(this.y);

    // Establishes how a line is created
    this.line = d3.line()
        .curve(d3.curveMonotoneX)
        .x( (d) => {
            return this.x(d.Date); })
        .y( (d) => {
            return this.y(d[curkey]); });

    // Use if line has multiple parts
    this.multLine = d3.line()
        .curve(d3.curveMonotoneX)
        .x( (d) => {
            return this.x(d.Date); })
        .y( (d) => {
            return this.y(d[curkey][WO]); });

    d3.select('svg').append('g')
        .attr('id','keyContainer')
        .attr('transform','translate('+this.margin.left+','+(this.height)+')');
}

MetricsGraph.prototype.computeSize = function(container)
{
    this.margin = {
        left : 70,
        right : 50,
        top : 80,
        bottom : 50
    }
    this.height = container.clientHeight;
    this.width = container.clientWidth;
}
MetricsGraph.prototype.mousemove = function(xPos)
{
    xPos = xPos -  this.margin.left - 8 - this.container.getBoundingClientRect().x;

    // Update infoBox
    var xDate = this.x.invert(xPos);

    formatInt = d3.format(",d");
    formatFloat = d3.format(".1f");


    dateBisect = d3.bisector(function(d, x){return d.Date - x} ).right;
    for(i in this.dataObjs)
    {
        var cur = this.dataObjs[i];
        var curInfoBox = cur.infoBox.element;

        if(cur.bars !== null && cur.bars.isMult) // if it's a multi bar graph
        {
            curInfoBox.style('visibility', 'hidden');
            return;
        }
        var idx = dateBisect(cur.data, xDate);
        // Prevent bisect from being last element
        if(idx >= cur.data.length)
        {
            var idx = cur.data.length-1; // 0 based;
        }
        //console.log(idx + "|||" + cur.data.length);
        if(this.config.graph.type == 'line')
        {
            var closestDot = d3.select(cur.dots.nodes()[idx]);
            var cx = (closestDot.attr('cx') );
            var cy = closestDot.attr('cy') //- closestDot.attr('height'));
            cx = parseFloat(cx);
        }
        else if(this.config.graph.type == 'bar')
        {
            var closestDot = d3.select(cur.bars.nodes()[idx]);
            var cx = (closestDot.attr('x') );
            var cy = closestDot.attr('y');
            var barWidth = parseFloat(closestDot.attr('width').replace('px', ''))
            cx = parseFloat(cx) + barWidth/2;
        }
        var dataValue = cur.data[idx][curkey];
        dataValue = Math.round(dataValue * 100) / 100;
        if(cx != cur.infoBox.cx) // if new closest dot
        {
            curInfoBox.style('visibility', 'visible')
                .transition()
                .attr('transform', 'translate('+cx+','+cy+')');
            if(isInt(dataValue))
                var displayValue = formatInt(dataValue);
            else
                var displayValue = formatFloat(dataValue)
            var rectWidth = getTextWidth((displayValue+"").length, 10);
            curInfoBox.select('rect')
                .attr('width', rectWidth)
                .attr('x', -rectWidth/2); // Center rect
            //console.log(dataValue)
            curInfoBox.select('text')
                .style('font-size', '16px')
                .text(displayValue);
            cur.infoBox.cx = cx
        }
    }
}

function isInt(n) {
    return n % 1 === 0;
}
/**
 * Places SVG in container. Additionally puts rect to capture mouse events
 */
MetricsGraph.prototype.placeSVG = function(container)
{
    this.container = container;
    var svg = d3.select(container).append("svg")
        .attr("width", this.width)
        .attr("height", this.height);

    // Append rect to receive mouse movements.
    svg.append('rect')
        .attr('width', this.width)
        .attr('height', this.height)
        .style('fill', 'rgba(255,255,255,0)')
        .on('mousemove', () => {var x = d3.event.x; this.mousemove(x)});

    // svg will be a 'g' element floated to give margin
    this.svg = svg.append("g")
        .attr("transform", "translate(" + this.margin.left + ","+this.margin.top+")");
}
function getTextWidth(numChars, value)
{
    if(value === undefined)
        value = 11.8;
    return numChars * value; // Should probably be non-linear
}

/**
 * RankingsGraph Class
 * ------------------
 * Initializes Rankings graph.
 */
function RankingsGraph(container, jsonFilename, gcurkey, title)
{
    this.container = container;
    this.initConfig();
    this.computeSize(this.container);
    this.placeSVG(this.container);
    initDefs(this.svg)
    curkey = gcurkey
    this.mykey = gcurkey;
    
    this.title = title;
    this.drawLargeTitle(title);
    this.color = this.getColorScheme()
    var descWidth = this.width/2; // Initial width of the rects
    //var descWidth = 200; // Initial width of the rects
    var leftMargin = this.margin.left;
    d3.json(jsonFilename).then( (data) =>
        {
            this.getKeys(data);
            curkey = this.mykey;
            if(curkey == null)
            {
                curkey = this.keys[0];
                this.mykey = curkey
            }
            this.drawTitle(curkey);
            this.data = data;
            // First sort by value of current key
            sortedData = data.sort(function(a,b){
                if(isNaN(a[curkey]))
                    a[curkey] = 0;
                if(isNaN(b[curkey]))
                    b[curkey] = 0;
                return b[curkey] - a[curkey];

            });
            // get array of values
            vals = sortedData.map(x => {return parseInt(x[curkey]);});

            // Calc and draw totals
            var total = sum(vals);
            var override = this.getOverridenTotal()
            if(override !== undefined)
                total = override;
            this.updateTotal(total)

            maxVal = Math.max(...vals);
            minVal = Math.min(...vals);
            maxWidth =  (this.width - this.margin.left-this.margin.right - descWidth);
            //minWidth =  (this.width - this.margin.left-this.margin.right)*.1; //.9 is fraction of max width
            minWidth = 0;
            scale = d3.scaleLinear()
                .range([minVal,maxVal])
                .domain([minWidth, maxWidth]);

            // Bind data to a <g>
            holders = this.svg.selectAll('.holder')
                .data(data)
                .enter()
                .append('g')
                .classed('holder', 'true')
                .style('cursor', 'pointer')
                .style('display', function(d,i) {
                    if(i >= 20) // max num
                        return 'none';
                    return 'block';
                })
                .attr('transform', (d,i) => {
                    var yTranslate = ((i*(this.config.graph.rectH+1))+this.config.graph.topMargin);
                    return "translate(0,"+yTranslate+")"
                });
            var self1 = this;
            holders // Actual bar + anchor to dataset homepage
                .append('rect')
                .classed('dataRect', true)
                .attr('height', '2')
                .attr('y', 14)
                .attr('x', descWidth)
                .attr('width', function(d){return scale.invert(d[curkey])})
                .style('fill',(d,i)=>{
                    colorFormula = ((i%20)/20);
                    return this.color(colorFormula);
                });
            var valueMargin = 5;
            holders // Description Bar
                .append('clipPath').attr('id', function(d,i){return 'rectClip'+i})
                .append('rect')
                .attr('class', 'rectClipEle')
                .attr('height', this.config.graph.rectH)
            //.attr('y', 14)
                .attr('x', -this.margin.left)
                .attr('width', descWidth + this.margin.left);
            holders // Description Bar
                .append('a')
                .attr('href', function(d){
                    if('dataset' in d)
                        return '/datasets/'+d.dataset;
                    return "https://google.com/search?q="+d.OName;
                })
                .attr('target', '#')
                .attr('title', "Click here to see dataset homepage")
                .attr('alt', "Click here to see dataset homepage")
                .append('rect')
                .attr('height', this.config.graph.rectH)
            //.attr('y', 14)
            //.attr('rx', '5px')
                .attr('x', -this.margin.left)
                .attr('width', descWidth + this.margin.left)
                .style('fill',(d,i)=>{
                    colorFormula = ((i%20)/20)*.8; // The .8 is to reduce range of color
                    return this.color(colorFormula);
                })
                .on('mouseover', function(){
                    var selectedRect = d3.select(this);
                    var gElement = d3.select(selectedRect.node().parentNode.parentNode)
                    gElement.select('.rectClipEle')
                        .transition()
                        .attr('width',maxWidth+descWidth+leftMargin)
                    gElement.select('.numText')
                        .transition()
                        .attr('x', maxWidth+descWidth +valueMargin)
                    selectedRect
                        .transition()
                        .attr('width',maxWidth+descWidth+leftMargin);
                })
                .on('mouseout', function(){
                    var self2 = self1
                    var selectedRect = d3.select(this);
                    var gElement = d3.select(selectedRect.node().parentNode.parentNode)
                    gElement.select('.rectClipEle')
                        .transition()
                        .attr('width',descWidth+leftMargin)
                    gElement.select('.numText')
                        .transition()
                        .attr('x', function(d){ return scale.invert(d[self2.mykey]) + descWidth + valueMargin})
                    selectedRect.transition().attr('width', leftMargin + descWidth)
                });
            holders.append('text') // Numbers to right of bar
                .classed('numText', true)
                .style('fill', 'black')
                .style('font-family', 'sans-serif')
                .style('font-weight', '800')
                .style('dominant-baseline', 'hanging')
                .style('text-anchor', 'start')
                .attr('y', '10')
                .attr('x', function(d){return scale.invert(d[curkey]) + descWidth + valueMargin})
                .text(function(d){
                    if(typeof(d[curkey]) == "string" && ! d[curkey].includes('.'))
                        return d[curkey];
                    return parseInt(d[curkey])});
            holders.append('circle') // Numbers to right of bar
                .classed('dataCircle', true)
                .style('fill',(d,i)=>{
                    colorFormula = ((i%20)/20)*.8; // The .8 is to reduce range of color
                    return this.color(colorFormula)})
                .attr('r', '6')
                .attr('cy', '15')
                .attr('cx', function(d){return scale.invert(d[curkey]) + descWidth - 3})
            holders.append('text') // Name on the bar
                .attr('y', '7')
                .attr('x', -this.margin.left + 5)
                .classed('descriptionText', true)
                .style('fill', 'white')
                .style('text-shadow','2px 2px #333')
                .style('font-family', 'Verdana')
                .style('pointer-events', 'none')
                .attr('clip-path', function(d,i){return 'url(#rectClip'+i+')'})
            //.style('font-weight', '800')
                .style('dominant-baseline', 'hanging')
                .text(function(d){
                    if('dataset' in d)
                        return ''+d.dataset+' -  '+d.OName;
                    return ""+d.OName;
                });
            drawSortByMenu(this.svg,this.keys, -this.margin.left,-10, function(){
                myGraph.reSort(d3.select(this).attr('data'));
            });
        });

    this.dataObjs = [];
    curkey = undefined;
}
/**
 * Returns a function that gets a color given a number
 */
RankingsGraph.prototype.getColorScheme = function()
{
    //this.color = d3.interpolateMagma;
    //this.color = d3.interpolatePlasma;
    //this.color = function(x){return d3.interpolateOranges((1-(x*.7)))};
    //this.color = function(x){return '#ddd'};
    //this.color = d3.interpolateCubehelixDefault
    //this.color = d3.scaleOrdinal(d3.schemeSet3).domain(20);
    //this.color = d3.scaleOrdinal(this.colorscheme).domain(20);
    //return function(x){return d3.interpolateWarm(((x*.7)))};
    return function(x){return d3.interpolateBlues(.9-(x*.4))};
}
RankingsGraph.prototype.getOverridenTotal = function()
{
    for(i in this.config.totals.overrideKey)
    {
        if(i == curkey)
            return this.config.totals.overrideKey[i];
    }
    return undefined;
}
/**
 *  Initializes object level configuration which modifies functionality.
 */
RankingsGraph.prototype.initConfig = function()
{
    this.config = {
        'totals' : {
            'totalsString' : 'RDA Total',
            'overrideKey' : { // Place key's where you want to override a value
                // e.g.
                //'Number of Users per Country' : 'one million'
            }
        },
        'graph' : {
            rectH : 30, // Height of Rects
            topMargin : 50 // Room above rects
        }

    };
}

/**
 * Searches data for all keys
 */
RankingsGraph.prototype.getKeys = function(data)
{
    this.keys = [];
    for(i in data)
    {
        var obj = data[i];
        var allKeys = Object.keys(obj);
        for(keyI in allKeys)
        {
            var key = allKeys[keyI];
            if(this.keys.indexOf(key) < 0 )
            {
                this.keys.push(key);
            }
        }
    }
    popElement(this.keys,'dataset');
    popElement(this.keys,'OName');
    popElement(this.keys,'index');
}
RankingsGraph.prototype.reSort = function(key)
{
    curkey = key;
    var valueMargin = 5;
    var descWidth = this.width/2;
    sortedData = this.data.sort(function(a,b) {
        if(isNaN(a[curkey]))
        {
            a[curkey] = 0;
        }
        if(isNaN(b[curkey]))
        {
            b[curkey] = 0;
        }
        return b[curkey] - a[curkey];
    });
    vals = sortedData.map(x => {return parseInt(x[curkey]);});
    var maxVal = Math.max(...vals);
    var minVal = Math.min(...vals);
    var maxWidth =  (this.width - this.margin.left-this.margin.right - descWidth);
    //var minWidth =  (this.width - this.margin.left-this.margin.right)* .1;
    var minWidth =  0;
    scale = d3.scaleLinear()
        .range([minVal,maxVal])
        .domain([minWidth, maxWidth]);
    holders.sort(function(a,b){return b[curkey] - a[curkey]})
        .transition()
        .duration(750)
        .attr('transform', (d,i) => {
            return "translate(0,"+((i*(this.config.graph.rectH+1))+this.config.graph.topMargin)+")";
        })
        .style('display', function(d,i) { if(i>19) return 'none'; return 'block';});
    holders.selectAll('.dataRect')
        .transition()
        .duration(750)
        .delay(750)
        .attr('width', function(d){return scale.invert(d[curkey])});
    holders.selectAll('.numText')
        .text(function(d){
            if(typeof(d[curkey]) == "string" && ! d[curkey].includes('.'))
                return d[curkey];
            return parseInt(d[curkey])
        })
        .transition()
        .duration(750)
        .delay(750)
        .attr('x', function(d){return scale.invert(d[curkey]) + descWidth + valueMargin});
    holders.selectAll('.dataCircle')
        .transition()
        .duration(750)
        .delay(750)
        .attr('cx', function(d){return scale.invert(d[curkey]) + descWidth - 3});
    this.drawTitle(curkey);

    var leftMargin = this.margin.left;
    // Update totals
    var total = sum(vals);
    this.updateTotal(total)

}
/**
 * Updates total if needed
 */
RankingsGraph.prototype.updateTotal = function(total)
{
    // This has hardcoded filepaths/variable names and is not good design.
    if(curkey == "Total Number of Unique Users")
    {
        isMonthlyRanking = this.title.includes('Month');
        if(isMonthlyRanking)
        {
            this.getMonthTotalFromFile();
        }
        else
        {
            this.getYearTotalFromFile();
        }
    }
    else
    {
        this.drawTotal(total,guessUnits(curkey));
    }
}
RankingsGraph.prototype.getMonthTotalFromFile = function()
{
    var total = 0;
    var curDate = new Date();
    curYear = curDate.getFullYear();
    curMonth = curDate.getMonth(); // 0 based, which is good since we want previous month
    if(curMonth == 0) // Account for January
    {
        curMonth = 11;
        curYear -= 1;
    }
    var lastMonthDate = curYear+'-'+padMonth(curMonth);
    allfile = '/media/metrics/json/'+curYear+'_all.json';
    d3.json(allfile).then( (data) =>
        {
            console.log(this)
            var arrData = convertToArray(data);
            var totalObj = null;
            console.log(lastMonthDate);
            for(var j in arrData)
            {
                if(arrData[j].Date == lastMonthDate)
                {
                    totalObj = arrData[j];
                    break;
                }
            }
            console.log(totalObj);
            totalObj = totalObj['Methods by Unique User'];
            for(var i in totalObj) // Loop through each method.
            {
                total += totalObj[i];
            }
            this.drawTotal(total,guessUnits(curkey));
        });
}
RankingsGraph.prototype.getYearTotalFromFile = function()
{
    var curDate = new Date();
    curYear = curDate.getFullYear();
    curMonth = curDate.getMonth();
    allfile = '/media/metrics/json//all10years.json';
    if(curMonth < 6) // Get last year's value if before June
    {
        curYear -= 1;
    }
    d3.json(allfile).then( (data) =>
        {
            var arrData = convertToArray(data);
            var total = 0;
            for(var j in arrData)
            {
                if(arrData[j].Date == curYear)
                {
                    totalObj = arrData[j];
                    break;
                }
            }
            totalObj = totalObj['Methods by Unique User'];
            for(var i in totalObj) // Loop through each method.
            {
                total += totalObj[i];
            }
            this.drawTotal(total,guessUnits(curkey));
        });
}
/**
 * pad zeros
 */
function padMonth(month)
{
    if((""+month).length == 1)
        return '0'+month;
    return month
}
RankingsGraph.prototype.clear = function()
{
    d3.selectAll('svg').remove();
}
RankingsGraph.prototype.drawLargeTitle = function(title)
{
    d3.select(this.svg.node().parentNode).append('text')
        .attr('id', 'largeTitle')
        .attr('x', this.width/2)
        .style('dominant-baseline', 'hanging')
        .style('text-anchor', 'middle')
        .style('text-decoration', 'underline')
        //.style('font-size', '2em')
        .text(title);
}
RankingsGraph.prototype.drawTotal = function(total, units)
{
    if(this.width < 400)
    {
        return;
    }
    var width = 150;
    var height = 50;
    this.svg.select('#total').remove();
    curG = this.svg.append('g')
        .attr('id', 'total')
        .attr('transform', 'translate('+(this.width - width - this.margin.right - this.margin.left)+', -10)');
    curG.append('rect')
        .attr('rx', '10px')
        .attr('ry', '10px')
        .attr('width', width)
        .attr('height', height)
        .style('stroke', 'gray')
        .style('stroke-width', '2px')
        .style('fill', 'white');
    textSize = 16;
    curG.append('text')
        .attr('x', width/2)
        .attr('y', (height/2)-2 )
        .style('font-size', textSize+'px')
        .style('text-anchor', 'middle')
        .style('text-decoration', 'underline')
        .style('font-weight', '800')
        .text(this.config.totals.totalsString)
    var text = curG.append('text')
        .attr('x', width/2)
        .attr('y', (height/2)+textSize)
        .style('font-size', '14px')
        .style('text-anchor', 'middle')
    if(units === undefined)
        text.text(total + "");
    else
        text.text(total + ' ' + units);

}
RankingsGraph.prototype.drawTitle = function(title)
{
    this.svg.select('#title').remove();
    this.svg.append('text')
        .attr('x', this.width/2 - this.margin.right)
        .attr('y', '-20px')
        .style('text-anchor', 'middle')
        .style('font-size', '1.1em')
        .style('font-weight', '800')
        .attr('id', 'title')
        .text(title);
}
RankingsGraph.prototype.computeSize = function(container)
{
    this.margin = {
        left : 60,
        right : 50,
        top : 70,
        bottom : 60
    }
    this.height = container.clientHeight;
    this.width = container.clientWidth;
}
RankingsGraph.prototype.placeSVG = function(container)
{
    var svg = d3.select(container).append("svg")
        .attr("width", this.width)
        .attr("height", this.height);
    svg.append('rect')  // append rect to recieve mouse movements
        .attr('width', this.width)
        .attr('height', this.height)
        .style('fill', 'none');
    this.svg = svg.append("g")
        .attr("transform", "translate(" + this.margin.left + ","+this.margin.top+")");
}
////////////////////
// Common functions
////////////////////

function drawSortByMenu(container, sortByArr, x, y, callback)
{
    // Example
    //
    //drawSortByMenu(myGraph.svg,['Total Number of Unique Users', 'Total Volume Downloaded (TB)'], 10,10, function(){console.log(d3.select(this).attr('data')); myGraph.reSort(d3.select(this).attr('data'))});
    //
    //
    if(sortByArr.length == 1)
        return;
    var width = 200;
    var height = 50;
    var parentSort = container.append('g')
        .attr('id', 'parentSort');

    var sortbyContainer = parentSort
        .append('g')
        .attr('id', 'sortByG')
        .attr('transform', 'translate('+x+','+y+')')
        .style('cursor', 'pointer')
        .on('mouseover', function()
            {
                // expand rect, show sort by
                d3.select(this).select('#sortByBox')
                    .style('fill', 'url(#grad2)');
                d3.select(this).selectAll('.sortOpt').style('visibility', 'visible');
            }
        )
        .on('mouseout', function(){
            d3.select(this).select('#sortByBox')
                .style('fill', 'url(#grad1)');
            d3.select(this).selectAll('.sortOpt').style('visibility', 'hidden');
            // close rect, show sort by
        });

    var curY = height-3;
    for(i in sortByArr)
    {
        var curName = sortByArr[i];
        //sortByContainer = d3.select('#sortByG');
        sortbyContainer.append('rect')
            .classed('sortOpt', true)
            .attr('width', width)
            .attr('height', height)
            .attr('y', curY)
            .attr('data', curName)
            .style('fill', '#eee')
            .style('visibility', 'hidden')
            .on('click', callback);
        sortbyContainer.append('text')
            .classed('sortOpt', true)
            .attr('x', width/2)
            .attr('y', curY+(height/2)-8)
            .style('pointer-events', 'none')
            .style('dominant-baseline', 'hanging')
            .style('text-anchor', 'middle')
            .style('visibility', 'hidden')
            .style('font-family', 'verdana')
        //.attr('textLength', width)
            .style('font-size', function(){
                if(curName.length>18 && curName.length < 50)
                    return (18-(curName.length/4)) + 'px';
                if(curName.length>=50)
                    return (18-(curName.length/5)) + 'px';
                return '18px';
            })
            .text(curName);
        curY += height;
    }
    sortbyContainer.append('rect')
        .attr('id', 'sortByBox')
        .attr('width', width)
        .attr('height', height)
        .attr('rx', 5)
        .attr('ry', 5)
        .style('fill', 'url(#grad1)')
        .style('stroke', '#bbb');
    var text = sortbyContainer.append('text')
        .attr('x', width/2)
        .attr('y', (height/2)-8)
        .style('dominant-baseline', 'hanging')
        .style('text-anchor', 'middle')
        .style('font-family', 'verdana')
        .style('pointer-events', 'none')
        .style('font-size', '18px');
    text.append('tspan').text('▾   ') // ' ' is not a space, but a unicode char
        .style('fill', '#e1e1e1');
    text.append('tspan').text('Sort By ');
    text.append('tspan').text('   ▾') // ' ' is not a space, but a unicode char
        .style('fill', '#e1e1e1');
    return sortbyContainer
}
function removeSortByMenu()
{
    d3.selectAll('#sortByG').remove();
}
///////////////
// initDefs
// Places gradient definitions in the svg.
// This is needed as you need gradient elements in svg
function initDefs(container)
{
    var defs = container.append('defs');
    var grad1 = defs.append('linearGradient')
        .attr('id', 'grad1')
        .attr('x1', '0')
        .attr('x2', '0')
        .attr('y1', '0')
        .attr('y2', '1');
    grad1.append('stop')
        .attr('offset', '25%')
        .attr('stop-color', 'white');
    grad1.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', '#ddd');

    var grad2 = defs.append('linearGradient')
        .attr('id', 'grad2')
        .attr('x1', '0')
        .attr('x2', '0')
        .attr('y1', '0')
        .attr('y2', '1');
    grad2.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', '#f1f1f1');
    grad2.append('stop')
        .attr('offset', '25%')
        .attr('stop-color', '#eee');
    grad2.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', '#ccc');

    var grad3 = defs.append('radialGradient')
        .attr('id', 'grad3')
        .attr('cy', '1')
        .attr('cx', '0');
    grad3.append('stop')
        .attr('offset', '80%')
        .attr('stop-color', 'rgb(0,0,0)');
    grad3.append('stop')
        .attr('offset', '95%')
        .attr('stop-color', 'rgba(0,0,0,0)');
}
function guessUnits(str)
{
    var arr = str.split(" ");
    return arr[arr.length-1];
}
function sum(arr)
{
    var tot = 0;
    for(i in arr)
    {
        tot += arr[i];
    }
    return tot;
}
///////////////////////
// popElement(arr, ele)
//
// If element matches ele, remove index from array,
// Otherwise, do nothing
function popElement(arr, ele)
{
    index = arr.indexOf(ele);
    if (index > -1) {
        arr.splice(index, 1);
    }
}
///////////////////
// convertDataSize
//
// Given array of data objects,
// 1. Find (guess) keys that include data size (MB, GB, ...)
// 2. Change key to best representation
// 3. Convert Value to reflect new key
// Note: all keys should be the same in every object
function convertDataSize(data, units)
{
    // First find keys that have MB, GB, etc in them
    dataKeys = [];
    unitKeys = [];
    unitRegex = /\((.*)\)/;
    tmpObj = data[0]; // This assumes each object has identical keys
    unitStr = "";
    for(var key in tmpObj)
    {
        keyArr = key.split(' ');
        lastEle = keyArr[keyArr.length-1];
        outArr = unitRegex.exec(lastEle);
        if(outArr)
        {
            unitKeys.push(outArr[1]); // first group in regex
            dataKeys.push(key);
        }
    }

    // Find Max value
    var maxes = [];
    for(var i in dataKeys)
    {
        var max = 0;
        curKey = dataKeys[i];
        for(var j in data)
        {
            var value = data[j][curKey];
            if(value instanceof Object)
            {
                value = d3.sum(Object.values(value)) // could be d3.max?
            }
            if(value > max)
            {
                max = value;
            }
        }
        maxes.push(max);
    }

    // Create new key with correct unit and value
    for(var i in maxes)
    {
        var max = maxes[i];
        ret = getConvertSize(max, unitKeys[i], units);
        convertFunc = ret[0];
        unitStr = ret[1];

        var key = dataKeys[i];
        tmpArr = key.split(' ');
        tmpArr[tmpArr.length-1] = '('+unitStr+')';
        newKey = tmpArr.join(' ')
        if(newKey != key)
        {
            for( var j in data )
            {
                curObj = data[j];
                oldVal = curObj[key];
                if(oldVal instanceof Object)
                {
                    tmpDict = {};
                    for(var objkey in oldVal)
                    {
                        tmpDict[objkey] = convertFunc(oldVal[objkey]);
                    }
                    newVal = tmpDict;
                }
                else
                {
                    newVal = convertFunc(oldVal);
                }
                curObj[newKey] = newVal;
                delete curObj[key];
            }
        }
    }
    return [data, unitStr];
}
/////////////////
// getConvertSize
//
// value - Likely a max value
// fromSize - 'GB', 'MB', 'TB', 'PB'
//            Defaults to 'GB'
// units - Forces units
//
// returns array where:
// index 0 is a function to convert value
// index 1 is name of new unit
//
function getConvertSize(value, fromSize, units)
{
    if(fromSize === undefined)
        fromSize = 'GB';
    // Transform to GB
    if(fromSize == 'MB')
        adjustFactor = .001;
    else if(fromSize == 'GB')
        adjustFactor = 1;
    else if(fromSize == 'TB')
        adjustFactor = 1000;
    else if(fromSize == 'PB')
        adjustFactor = 1000000;
    else
        adjustFactor = 1;

    value = value * adjustFactor;

    if(units == "MB" || (value < 1 && units === undefined)) // to MB
        return [function(inVal){return inVal * 1000;},'MB'];
    if(units == "PB" || (value > 1000000 && units === undefined)) // to PB
        return [function(inVal){return inVal * .000001;},'PB'];
    if(units == "TB" || (value > 1000 && units === undefined)) // to TB
        return [function(inVal){return inVal * .001;},'TB'];

    return [function(inVal){return inVal;},'GB'];
}

//Swap values with keys in an object/dict.
//Repeating values will cause unexpected behaviors
function swap(dict){
    var ret = {};
    for(var key in dict)
    {
        ret[dict[key]] = key;
    }
    return ret;
}

// Convert dict to array.
// Removes key
function convertToArray(dict)
{
    if(typeof(dict) != typeof({}))
    {
        return dict;
    }
    var temp = [];
    for(i in dict)
    {
        temp.push(dict[i]);
    }
    temp = temp.sort(function(a,b) {
        da = new Date(a.Date);
        db = new Date(b.Date);
        return da - db;
    });
    return temp;
}

// Convert dict to array.
// Removes key
function convertToArrayWithKey(dict)
{
    ayyy=dict;
    var temp = [];
    for(i in dict)
    {
        var obj = {};
        obj[i] = dict[i];
        temp.push(obj);
    }
    return temp;
}
function getAllKeys(data)
{
    tmp_keys = [];
    for(i in data)
    {
        var obj = data[i];
        var allKeys = Object.keys(obj);
        for(keyI in allKeys)
        {
            var key = allKeys[keyI];
            if(tmp_keys.indexOf(key) < 0 )
            {
                tmp_keys.push(key);
            }
        }
    }
    return tmp_keys;
}

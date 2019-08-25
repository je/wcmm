var l = document.getElementById('left');
l.innerHTML += 'Wilderness Character Monitoring Measures';

var r = document.getElementById('right');
r.innerHTML += '{{name}}';

var map = L.map('map', {
    zoom: 7,
    preferCanvas: true,
    maxBounds: [[-90, -200], [90, 180]],
    maxZoom: 17,
    minZoom: 2,
    fullscreenControl: true,
    fullscreenControlOptions: {
       position: 'bottomleft'
    },
    attributionControl: false,
    attributionControlOptions: {
       prefix: ''
    },
    zoomControl: true,
});

$.getJSON('/s/wcm/{{slug}}/{{slug}}.json.packed').done(addTopoData);

L.TopoJSON = L.GeoJSON.extend({
  addData: function(jsonData) {    
    if (jsonData.type === "Topology") {
      for (key in jsonData.objects) {
        geojson = topojson.feature(jsonData, jsonData.objects[key]);
        L.GeoJSON.prototype.addData.call(this, geojson);
      }
    }    
    else {
      L.GeoJSON.prototype.addData.call(this, jsonData);
    }
  }  
});

topoLayer = new L.TopoJSON(null, {
    style: function(feature) {
        return { 
            color: 'Black',
            fillColor:  'HotPink',
            fillOpacity: 0.0,
            weight: 1.5,
            opacity: 1
        };
    },
});

function addTopoData(topoData){
    topoLayer.addData(topoData);
    topoLayer.addTo(map);
    map.fitBounds(topoLayer.getBounds());

    var cFull = L.control({
        position: 'bottomleft'
    });
    cFull.onAdd = function(map) {
        var div = L.DomUtil.create('div', 'leaflet-control-zoom leaflet-bar leaflet-control');
        div.id += 'full-extent-btn';
        div.innerHTML += '<a class="leaflet-control-zoom-home home-icon" href="#" title="Full extent" role="button" aria-label="Full extent"><span class=\'glyphicon glyphicon-bookmark small\'></span></a>';
        return div;
    };
    cFull.addTo(map);

    $("#full-extent-btn").click(function() {
      map.fitBounds(topoLayer.getBounds());
      return false;
    });
}

var frem = "<span class='' style='color:Black'><strong>Remoteness Downloads</strong></span><br><a href='{{slug}}-rem-in-fin.png'>inside remoteness map</a> <span class='pull-right'>with <a href='{{slug}}-rem-in-fin-base.png'>terrain</a> and <a href='{{slug}}-rem-in-fin-by-own-base.png'>by usfs/blm ownership</a></span><br><a href='{{slug}}-rem-out-fin.png'>outside remoteness map</a> <span class='pull-right'>with <a href='{{slug}}-rem-out-fin-base.png'>terrain</a> and <a href='{{slug}}-rem-out-fin-by-own-base.png'>by usfs/blm ownership</a></span><br><a href='{{slug}}-rem-all-fin.png'>combined remoteness map</a> <span class='pull-right'>with <a href='{{slug}}-rem-all-fin-base.png'>terrain</a></span><br><a href='{{slug}}-rem-all-fin-27in.png'>combined remoteness map 27\"</a> <span class='pull-right'>with <a href='{{slug}}-rem-all-fin-27in-base.png'>terrain</a></span>";

var fair = "<span class='' style='color:Black'><strong>Air Quality Downloads</strong></span><br><a href='{{slug}}-ntdep.png'>nitrogen deposition trend map</a> <span class='pull-right'>with <a href='{{slug}}-ntdep-base.png'>terrain</a> and <a href='{{slug}}-ntdep-base-own.png'>usfs/blm ownership</a></span><br><a href='{{slug}}-ntdep-graph.png'>nitrogen deposition trend graph</a>{% if nt_ext %}<br><a href='{{nt_ext}}'>nitrogen deposition trend graph extended</a>{% endif %}<br><a href='{{slug}}-ntdep.csv'>nitorgen deposition trend csv</a><br><a href='{{slug}}-stdep.png'>sulfur deposition trend map</a> <span class='pull-right'>with <a href='{{slug}}-stdep-base.png'>terrain</a> and <a href='{{slug}}-stdep-base-own.png'>usfs/blm ownership</a></span><br><a href='{{slug}}-stdep-graph.png'>sulfur deposition trend graph</a>{% if st_ext %}<br><a href='{{st_ext}}'>sulfur deposition trend graph extended</a>{% endif %}<br><a href='{{slug}}-stdep.csv'>sulfur deposition trend csv</a>{% if vis_csv %}<br><a href='{{slug}}-visibility-graph.png'>visibility trend graph</a>{% endif %}{% if vis_ext %}<br><a href='{{vis_ext}}'>visibility trend graph extended</a>{% endif %}{% if vis_csv %}<br><a href='{{vis_csv}}'>visibility trend csv</a>{% endif %}</span>";

var fwat = "<span class='' style='color:Black'><strong>Water Quality Downloads</strong><br><a href='{{slug}}-streams.png'>impaired streams map</a> <span class='pull-right'>with <a href='{{slug}}-streams-base.png'>terrain</a> and <a href='{{slug}}-streams-base-own.png'>usfs/blm ownership</a></span><br><a href='{{slug}}-streams.csv'>impaired streams csv</a><br><a href='{{slug}}-lakes.png'>impaired lakes map</a> <span class='pull-right'>with <a href='{{slug}}-lakes-base.png'>terrain</a> and <a href='{{slug}}-lakes-base-own.png'>usfs/blm ownership</a></span><br><a href='{{slug}}-lakes.csv'>impaired lakes csv</a><br><a href='{{slug}}-303d.png'>impaired waterbodies map</a> <span class='pull-right'>with <a href='{{slug}}-303d-base.png'>terrain</a> and <a href='{{slug}}-303d-base-own.png'>usfs/blm ownership</a></span><br><a href='{{slug}}-wcc.png'>watershed condition map</a> <span class='pull-right'>with <a href='{{slug}}-wcc-base.png'>terrain</a> and <a href='{{slug}}-wcc-by-own-base.png'>by usfs/blm ownership</a></span><br><a href='{{slug}}-wcc.csv'>watershed condition csv</a></span>";

var pcs = {};
pcs.ro = "<span class='small' style='color:Black'><strong>Remoteness from development outside wilderness</strong><br>{{ io.w_ac }} wilderness acres<br>{{ io.o_ac }} outroads acres ({{ io.o_pct }}%)</span>";
pcs.ri = "<span class='small' style='color:Black'><strong>Remoteness from development inside wilderness</strong><br>{{ io.w_ac }} wilderness acres<br>{{ io.i_ac }} inroads acres ({{ io.i_pct }}%)</span>";
pcs.npc = "<span class='small' style='color:Black'><strong>Nitrogen total deposition trend inside wilderness</strong><br>latest tdep = {{ ntdep.endy }}<br>tdep trend = {{ ntdep.m }}<br>tdep trend p-value = {{ ntdep.p }}</span>";
pcs.spc = "<span class='small' style='color:Black'><strong>Sulfur total deposition trend inside wilderness</strong><br>latest tdep = {{ stdep.endy }}<br>tdep trend = {{ stdep.m }}<br>tdep trend p-value = {{ stdep.p }}</span>";
pcs.wspc = "<span class='small' style='color:Black'><strong>Impaired streams inside wilderness</strong><br>{{ iw.smiles }} miles impaired streams<br>{{ iw.smiles2 }} miles inventoried streams</span>";
pcs.wlpc = "<span class='small' style='color:Black'><strong>Impaired lakes inside wilderness</strong><br>{{ iw.slakes }} impaired lakes<br>{{ iw.slakes2 }} inventoried lakes</span>";
pcs.wcc = "<span class='small' style='color:Black'><strong>Watershed condition class</strong><br>{{ wcc.w_ac }} total wilderness acres<br>{{ wcc.ia_ac }} acres 'functioning properly' ({{ wcc.ia_pct }}%)<br>{{ wcc.ib_ac }} acres 'functioning at risk' ({{ wcc.ib_pct }}%)<br>{{ wcc.ic_ac }} acres 'impaired function' ({{ wcc.ic_pct }}%)" + "</span>";

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-out-fin.json.packed').done(addRO);

function style_ro(feature) {
    return {
        color: 'Cyan',
        fillColor:  'Cyan',
        fillOpacity: 0.4,
        weight: 1.5,
        opacity: 1
    };
}

function oneach_ro(feature, layer) {
    if (feature.properties) {
      var fc = "";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html('');
        }
      });
    }
}

tro = new L.TopoJSON(null, {style: style_ro, onEachFeature: oneach_ro});

function addRO(topoData){
    tro.addData(topoData);
    tro.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-roadcore2-out.json.packed').done(addROr);

function style_ror(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_ror(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>roadcore2 outside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html('');
        }
      });
    }
}

tror = new L.TopoJSON(null, {style: style_ror, onEachFeature: oneach_ror});

function addROr(topoData){
    tror.addData(topoData);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-devln-out.json.packed').done(addROdl);

function style_rodl(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_rodl(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>dev_ln outside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html('');
        }
      });
    }
}

trodl = new L.TopoJSON(null, {style: style_rodl, onEachFeature: oneach_rodl});

function addROdl(topoData){
    trodl.addData(topoData);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-devpt-out.json.packed').done(addROdd);

function style_rodd(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_rodd(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>dev_pt outside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html('');
        }
      });
    }
}

trodd = new L.TopoJSON(null, {style: style_rodd, onEachFeature: oneach_rodd,
    pointToLayer: function (feature, latlng) {
      return L.circleMarker(latlng, {
        radius: 1,
        fillColor: "Grey",
        color: "Gray",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
      });
    }
 });

function addROdd(topoData){
    trodd.addData(topoData);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-devpl-out.json.packed').done(addROdp);

function style_rodp(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_rodp(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>dev_pl outside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ro);
          $("#feat").html('');
        }
      });
    }
}

trodp = new L.TopoJSON(null, {style: style_rodp, onEachFeature: oneach_rodp});

function addROdp(topoData){
    trodp.addData(topoData);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-in-fin.json.packed').done(addRI);

function style_ri(feature) {
    return {
        color: 'HotPink',
        fillColor:  'HotPink',
        fillOpacity: 0.5,
        weight: 1.5,
        opacity: 1
    };
}

function oneach_ri(feature, layer) {
    if (feature.properties) {
      var fc = "";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html('');
        }
      });
    }
}

tri = new L.TopoJSON(null, {style: style_ri, onEachFeature: oneach_ri});

function addRI(topoData){
    tri.addData(topoData);
    tri.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-roadcore2-in.json.packed').done(addRIr);

function style_rir(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_rir(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>roadcore2 inside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html('');
        }
      });
    }
}

trir = new L.TopoJSON(null, {style: style_rir, onEachFeature: oneach_rir});

function addRIr(topoData){
    trir.addData(topoData);
    //trir.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-devln-in.json.packed').done(addRIdl);

function style_ridl(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_ridl(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>dev_ln inside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html('');
        }
      });
    }
}

tridl = new L.TopoJSON(null, {style: style_ridl, onEachFeature: oneach_ridl});

function addRIdl(topoData){
    tridl.addData(topoData);
    //tridl.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-devpt-in.json.packed').done(addRIdd);

function style_ridd(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_ridd(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>dev_pt inside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html('');
        }
      });
    }
}

tridd = new L.TopoJSON(null, {style: style_ridd, onEachFeature: oneach_ridd,
    pointToLayer: function (feature, latlng) {
      return L.circleMarker(latlng, {
        radius: 1,
        fillColor: "Grey",
        color: "Gray",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
      });
    }
 });

function addRIdd(topoData){
    tridd.addData(topoData);
    //tridd.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-rem-devpl-in.json.packed').done(addRIdp);

function style_ridp(feature) {
    return {
        color: 'Grey',
        weight: 1.5,
        opacity: 1
    };
}

function oneach_ridp(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>dev_pl inside wilderness</strong><br>" + feature.properties.id + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.ri);
          $("#feat").html('');
        }
      });
    }
}

tridp = new L.TopoJSON(null, {style: style_ridp, onEachFeature: oneach_ridp});

function addRIdp(topoData){
    tridp.addData(topoData);
    //tridp.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-ntdep-grid.json.packed').done(addN);

function oneach_ntdep(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Nitrogen total deposition trend in selected cell</strong><br>latest tdep = " + feature.properties.endy + "<br>tdep trend = " + feature.properties.m + "<br>tdep trend p-value = " + feature.properties.p_value + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.npc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.npc);
          $("#feat").html('');
        }
      });
    }
}

function style_ntdep(feature) {
    return {
        fillColor: 'white',
        weight: 1.5,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.8
    };
}

tnt = new L.TopoJSON(null, {style: style_ntdep, onEachFeature: oneach_ntdep});

function addN(topoData){
    tnt.addData(topoData);
    tnt.addTo(map);
    var nmax = -999999999;
    var nmin = 999999999;
    var nm = null;
    tnt.eachLayer(function(layer) {
        nm = layer.feature.properties['m'];
        if (nm > nmax) {
            nmax = nm;
        };
        if (nm < nmin) {
            nmin = nm;
        };
    });
    var nstep = (nmax - nmin) / 8
    tnt.eachLayer(function(layer) {
      if(layer.feature.properties.m >= nmax) {    
        layer.setStyle({fillColor :'#fee838'}) 
      }
      else if (layer.feature.properties.m > nmin + (7 * nstep)) {    
        layer.setStyle({fillColor :'#dec958'}) 
      }
      else if (layer.feature.properties.m > nmin + (6 * nstep)) {    
        layer.setStyle({fillColor :'#bcae6c'}) 
      }
      else if (layer.feature.properties.m > nmin + (5 * nstep)) {    
        layer.setStyle({fillColor :'#9b9476'}) 
      }
      else if (layer.feature.properties.m > nmin + (4 * nstep)) {    
        layer.setStyle({fillColor :'#7d7c78'}) 
      }
      else if (layer.feature.properties.m > nmin + (3 * nstep)) {    
        layer.setStyle({fillColor :'#61656f'}) 
      }
      else if (layer.feature.properties.m > nmin + (2 * nstep)) {    
        layer.setStyle({fillColor :'#434e6c'}) 
      }
      else if (layer.feature.properties.m > nmin + (1 * nstep)) {    
        layer.setStyle({fillColor :'#1a386f'}) 
      }
      else if (layer.feature.properties.m >= nmin) {    
        layer.setStyle({fillColor :'#00224e'}) 
      }
    });
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-stdep-grid.json.packed').done(addS);

function oneach_stdep(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Sulfur total deposition trend in selected cell</strong><br>latest tdep = " + feature.properties.endy + "<br>tdep trend = " + feature.properties.m + "<br>tdep trend p-value = " + feature.properties.p_value + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.spc);
          $("#feat").html(fc);
       },
        add: function (e) {
          $("#perims").html(pcs.spc);
          $("#feat").html('');
        }
      });
    }
}

function style_stdep(feature) {
    return {
        fillColor: 'white',
        weight: 1.5,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.8
    };
}

tst = new L.TopoJSON(null, {style: style_stdep, onEachFeature: oneach_stdep});

function addS(topoData){
    tst.addData(topoData);
    tst.addTo(map);
    var smax = -999999999;
    var smin = 999999999;
    var sm = null;
    tst.eachLayer(function(layer) {
        sm = layer.feature.properties['m'];
        if (sm > smax) {
            smax = sm;
        };
        if (sm < smin) {
            smin = sm;
        };
    });
    var sstep = (smax - smin) / 8
    tst.eachLayer(function(layer) {
      if(layer.feature.properties.m >= smax) {    
        layer.setStyle({fillColor :'#fee838'}) 
      }
      else if (layer.feature.properties.m > smin + (7 * sstep)) {    
        layer.setStyle({fillColor :'#dec958'}) 
      }
      else if (layer.feature.properties.m > smin + (6 * sstep)) {    
        layer.setStyle({fillColor :'#bcae6c'}) 
      }
      else if (layer.feature.properties.m > smin + (5 * sstep)) {    
        layer.setStyle({fillColor :'#9b9476'}) 
      }
      else if (layer.feature.properties.m > smin + (4 * sstep)) {    
        layer.setStyle({fillColor :'#7d7c78'}) 
      }
      else if (layer.feature.properties.m > smin + (3 * sstep)) {    
        layer.setStyle({fillColor :'#61656f'}) 
      }
      else if (layer.feature.properties.m > smin + (2 * sstep)) {    
        layer.setStyle({fillColor :'#434e6c'}) 
      }
      else if (layer.feature.properties.m > smin + (1 * sstep)) {    
        layer.setStyle({fillColor :'#1a386f'}) 
      }
      else if (layer.feature.properties.m >= smin) {    
        layer.setStyle({fillColor :'#00224e'}) 
      }
    });
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-streams.json.packed').done(addWis);

function style_wis(feature) {
    return {
        fillColor: 'red',
        weight: 1.5,
        opacity: 1,
        color: 'red',
        fillOpacity: 0.8
    };
}

function oneach_wis(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected impaired stream</strong><br>" + feature.properties.reachcode + " unnamed" + "<br>" + feature.properties.miles + " miles</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html('');
        }
      });
    }
}

twis = new L.TopoJSON(null, {style: style_wis, onEachFeature: oneach_wis});

function addWis(topoData){
    twis.addData(topoData);
    twis.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-streams-around.json.packed').done(addWisf);

function style_wisf(feature) {
    return {
        fillColor: 'red',
        weight: 1.0,
        opacity: 0.7,
        color: 'red',
        fillOpacity: 0.7
    };
}

function oneach_wisf(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected impaired stream</strong><br>" + feature.properties.reachcode + " unnamed</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html('');
        }
      });
    }
}

twisf = new L.TopoJSON(null, {style: style_wisf, onEachFeature: oneach_wisf});

function addWisf(topoData){
    twisf.addData(topoData);
    //twisf.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-streamsb.json.packed').done(addWsb);

function style_wsb(feature) {
    return {
        fillColor: 'blue',
        weight: 1.5,
        opacity: 1,
        color: 'blue',
        fillOpacity: 0.8
    };
}

function oneach_wsb(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected inventoried stream</strong><br>" + feature.properties.reachcode + " unnamed</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html('');
        }
      });
    }
}

twsb = new L.TopoJSON(null, {style: style_wsb, onEachFeature: oneach_wsb});

function addWsb(topoData){
    twsb.addData(topoData);
    //twsb.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-streamsb-around.json.packed').done(addWsba);

function style_wsba(feature) {
    return {
        fillColor: 'blue',
        weight: 1.0,
        opacity: 0.7,
        color: 'blue',
        fillOpacity: 0.7
    };
}

function oneach_wsba(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected inventoried stream</strong><br>" + feature.properties.reachcode + " unnamed</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wspc);
          $("#feat").html('');
        }
      });
    }
}

twsba = new L.TopoJSON(null, {style: style_wsba, onEachFeature: oneach_wsba});

function addWsba(topoData){
    twsba.addData(topoData);
    //twsba.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-lakes.json.packed').done(addWil);

function style_wil(feature) {
    return {
        fillColor: 'red',
        weight: 1.5,
        opacity: 1,
        color: 'red',
        fillOpacity: 0.8
    };
}

function oneach_wil(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected impaired lake</strong><br>" + feature.properties.reachcode + " " + "unnamed" + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html('');
        }
      });
    }
}

twil = new L.TopoJSON(null, {style: style_wil, onEachFeature: oneach_wil});

function addWil(topoData){
    twil.addData(topoData);
    twil.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-lakes-around.json.packed').done(addWilf);

function style_wilf(feature) {
    return {
        fillColor: 'red',
        weight: 1.0,
        opacity: 0.7,
        color: 'red',
        fillOpacity: 0.5
    };
}

function oneach_wilf(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected impaired lake</strong><br>" + feature.properties.reachcode + " " + "unnamed" + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html('');
        }
      });
    }
}

twilf = new L.TopoJSON(null, {style: style_wilf, onEachFeature: oneach_wilf});

function addWilf(topoData){
    twilf.addData(topoData);
    //twilf.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-lakesb.json.packed').done(addWlb);

function style_wlb(feature) {
    return {
        fillColor: 'blue',
        weight: 1.5,
        opacity: 1,
        color: 'blue',
        fillOpacity: 0.8
    };
}

function oneach_wlb(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected inventoried lake</strong><br>" + feature.properties.reachcode + " " + "unnamed" + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html('');
        }
      });
    }
}

twlb = new L.TopoJSON(null, {style: style_wlb, onEachFeature: oneach_wlb});

function addWlb(topoData){
    twlb.addData(topoData);
    //twlb.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-lakesb-around.json.packed').done(addWlba);

function style_wlba(feature) {
    return {
        fillColor: 'blue',
        weight: 1.0,
        opacity: 0.7,
        color: 'blue',
        fillOpacity: 0.5
    };
}

function oneach_wlba(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected inventoried lake</strong><br>" + feature.properties.reachcode + " " + "unnamed" + "</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wlpc);
          $("#feat").html('');
        }
      });
    }
}

twlba = new L.TopoJSON(null, {style: style_wlba, onEachFeature: oneach_wlba});

function addWlba(topoData){
    twlba.addData(topoData);
    //twlba.addTo(map);
}

$.getJSON('/s/wcm/{{slug}}/{{slug}}-wcc.json.packed').done(addWcc);

function gCwcc(d) {
    return d === 'Functioning Properly' ? 'Green' :
           d === 'Functioning at Risk' ? 'Orange' :
           d === 'Impaired Function' ? 'Red' :
                      'White';
}

function style_wcc(feature) {
    return {
        fillColor: gCwcc(feature.properties.wcc),
        weight: 1.5,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.7
    };
}

function oneach_wcc(feature, layer) {
    if (feature.properties) {
      var fc = "<span class='small' style='color:Black'><strong>Selected watershed condition class</strong><br>" + feature.properties.number + " " + feature.properties.name + "</span><br><span class='small'>" + feature.properties.wcc + "</span><br><span class='small'>" + feature.properties.acres + " acres in wilderness</span>";
      layer.on({
        click: function (e) {
          $("#perims").html(pcs.wcc);
          $("#feat").html(fc);
        },
        add: function (e) {
          $("#perims").html(pcs.wcc);
          $("#feat").html('');
        }
      });
    }
}

twcc = new L.TopoJSON(null, {style: style_wcc, onEachFeature: oneach_wcc});

function addWcc(topoData){
    twcc.addData(topoData);
    twcc.addTo(map);
}

var olsr = {
    "<i class='glyphicon glyphicon-stop' style='color:cyan'></i> Remoteness from outside development": tro,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> roadcore2 outside wilderness": tror,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> dev_ln outside wilderness": trodl,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> dev_pt outside wilderness": trodd,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> dev_pl outside wilderness": trodp,
    "<i class='glyphicon glyphicon-stop' style='color:hotpink'></i> Remoteness from inside development": tri,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> roadcore2 inside wilderness": trir,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> dev_ln inside wilderness": tridl,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> dev_pt inside wilderness": tridd,
    "<i class='glyphicon glyphicon-minus' style='color:grey'></i> dev_pl inside wilderness": tridp,
};

var olsn = {
    "<i class='glyphicon glyphicon-stop' style='color:#00224e'></i><i class='glyphicon glyphicon-stop' style='color:#7d7c78'></i><i class='glyphicon glyphicon-stop' style='color:#fee838'></i> Nitrogen total deposition trend": tnt,
    "<i class='glyphicon glyphicon-stop' style='color:#00224e'></i><i class='glyphicon glyphicon-stop' style='color:#7d7c78'></i><i class='glyphicon glyphicon-stop' style='color:#fee838'></i> Sulfur total deposition trend": tst,
};

var olsw = {
    "<i class='glyphicon glyphicon-minus' style='color:red'></i> Impaired streams inside wilderness": twis,
    "<i class='glyphicon glyphicon-minus' style='color:red'></i> impaired streams near wilderness": twisf,
    "<i class='glyphicon glyphicon-minus' style='color:blue'></i> inventoried streams inside wilderness": twsb,
    "<i class='glyphicon glyphicon-minus' style='color:blue'></i> inventoried streams near wilderness ": twsba,
    "<i class='glyphicon glyphicon-stop' style='color:red'></i> Impaired lakes inside wilderness": twil,
    "<i class='glyphicon glyphicon-stop' style='color:red'></i> impaired lakes near wilderness": twilf,
    "<i class='glyphicon glyphicon-stop' style='color:blue'></i> inventoried lakes inside wilderness": twlb,
    "<i class='glyphicon glyphicon-stop' style='color:blue'></i> inventoried lakes near wilderness": twlba,
    "<i class='glyphicon glyphicon-stop' style='color:green'></i><i class='glyphicon glyphicon-stop' style='color:orange'></i><i class='glyphicon glyphicon-stop' style='color:red'></i> Watershed condition class": twcc,
};

var mapicons = "<a href='#' id='ro-btn'><i class='glyphicon glyphicon-th' style='color:cyan'></i></a><a href='#' id='ri-btn'><i class='glyphicon glyphicon-th' style='color:hotpink'></i></a><a href='#' id='iw-btn'><i class='glyphicon glyphicon-th' style='color:red'></i></a><a href='#' id='wc-btn'><i class='glyphicon glyphicon-th' style='color:green'></i></a><a href='#' id='n-btn'><i class='glyphicon glyphicon-th' style='color:yellow'></i></a><a href='#' id='s-btn'><i class='glyphicon glyphicon-th' style='color:yellow'></i></a>"

var maps = L.control({
    position: 'topright'
});

maps.onAdd = function(map) {
    var div = L.DomUtil.create('div', 'info');
    div.id += 'maps';
    div.innerHTML += mapicons;
    return div;
};
//maps.addTo(map);

var baseLayers = getCommonBaseLayers(map);

rc = L.control.layers({}, olsr, {collapsed:false}).addTo(map);
wc = L.control.layers({}, olsw, {collapsed:false}).addTo(map);
ac = L.control.layers({}, olsn, {collapsed:false}).addTo(map);
L.control.layers(baseLayers, {}).addTo(map);

var info = L.control({
    position: 'topleft'
});
info.onAdd = function(map) {
    var div = L.DomUtil.create('div', 'info');
    div.id += 'perims';
    div.innerHTML += '<small></small>';
    return div;
};
info.addTo(map);

var info = L.control({
    position: 'topleft'
});
info.onAdd = function(map) {
    var div = L.DomUtil.create('div', 'info');
    div.id += 'feat';
    div.innerHTML += '<small></small>';
    return div;
};
info.addTo(map);

var files = L.control({
    position: 'bottomright'
});
files.onAdd = function(map) {
    var div = L.DomUtil.create('div', 'info');
    div.id += 'files';
    div.innerHTML += '<small><span="small" style="color:DarkGrey">revision.2019.04</span></small>';
    return div;
};
files.addTo(map);

$("#about-btn").click(function() {
  $("#aboutModal").modal("show");
  $(".navbar-collapse.in").collapse("hide");
  return false;
});

$("#frem").html(frem);
$("#fair").html(fair);
$("#fwat").html(fwat);

function r_ro() {
    map.removeLayer(tro);
    map.removeLayer(tror);
    map.removeLayer(trodl);
    map.removeLayer(trodd);
    map.removeLayer(trodp);
    $("#ro-btn").addClass('dim');
};

function a_ro() {
    map.addLayer(tro);
    map.addLayer(tror);
    map.addLayer(trodl);
    map.addLayer(trodd);
    map.addLayer(trodp);
    $("#ro-btn").removeClass('dim');
};

function r_ri() {
    map.removeLayer(tri);
    map.removeLayer(trir);
    map.removeLayer(tridl);
    map.removeLayer(tridd);
    map.removeLayer(tridp);
    $("#ri-btn").addClass('dim');
};

function a_ri() {
    map.addLayer(tri);
    map.addLayer(trir);
    map.addLayer(tridl);
    map.addLayer(tridd);
    map.addLayer(tridp);
    $("#ri-btn").removeClass('dim');
};

function r_iw() {
    map.removeLayer(twis);
    map.removeLayer(twisf);
    map.removeLayer(twsb);
    map.removeLayer(twsba);
    map.removeLayer(twil);
    map.removeLayer(twilf);
    map.removeLayer(twlb);
    map.removeLayer(twlba);
    $("#iw-btn").addClass('dim');
};

function a_iw() {
    map.addLayer(twsba);
    map.addLayer(twsb);
    map.addLayer(twlba);
    map.addLayer(twlb);
    map.addLayer(twisf);
    map.addLayer(twis);
    map.addLayer(twilf);
    map.addLayer(twil);
    $("#iw-btn").removeClass('dim');
};

$("#ro-btn").click(function() {
    a_ro();
    r_ri();
    r_iw();
    map.removeLayer(twcc);
    $("#wc-btn").addClass('dim');
    map.removeLayer(tnt);
    $("#n-btn").addClass('dim');
    map.removeLayer(tst);
    $("#s-btn").addClass('dim');
    $("#perims").html(pcs.ro);
    $("#feat").html('');
  return false;
});

$("#ri-btn").click(function() {
    r_ro();
    a_ri();
    r_iw();
    map.removeLayer(twcc);
    $("#wc-btn").addClass('dim');
    map.removeLayer(tnt);
    $("#n-btn").addClass('dim');
    map.removeLayer(tst);
    $("#s-btn").addClass('dim');
    $("#perims").html(pcs.ri);
    $("#feat").html('');
  return false;
});

$("#iw-btn").click(function() {
    r_ro();
    r_ri();
    a_iw();
    map.removeLayer(twcc);
    $("#wc-btn").addClass('dim');
    map.removeLayer(tnt);
    $("#n-btn").addClass('dim');
    map.removeLayer(tst);
    $("#s-btn").addClass('dim');
    $("#perims").html(pcs.wspc + '<br>' + pcs.wlpc);
    $("#feat").html('');
});

$("#wc-btn").click(function() {
    r_ro();
    r_ri();
    r_iw();
    map.addLayer(twcc);
    $("#wc-btn").removeClass('dim');
    map.removeLayer(tnt);
    $("#n-btn").addClass('dim');
    map.removeLayer(tst);
    $("#s-btn").addClass('dim');
    $("#perims").html(pcs.wcc);
    $("#feat").html('');
  return false;
});

$("#n-btn").click(function() {
    r_ro();
    r_ri();
    r_iw();
    map.removeLayer(twcc);
    $("#wc-btn").addClass('dim');
    map.addLayer(tnt);
    $("#n-btn").removeClass('dim');
    map.removeLayer(tst);
    $("#s-btn").addClass('dim');
    $("#perims").html(pcs.npc);
    $("#feat").html('');
  return false;
});

$("#s-btn").click(function() {
    r_ro();
    r_ri();
    r_iw();
    map.removeLayer(twcc);
    $("#wc-btn").addClass('dim');
    map.removeLayer(tnt);
    $("#n-btn").addClass('dim');
    map.addLayer(tst);
    $("#s-btn").removeClass('dim');
    $("#perims").html(pcs.spc);
    $("#feat").html('');
  return false;
});

const SPORTS = {
  nfl:{label:'NFL',icon:'🏈',background:'background-nfl.png',accent:'#d71920',country:'United States',league:'National Football League',detail:'Quarter · Clock · Possession · Down & distance'},
  nba:{label:'NBA',icon:'🏀',background:'background-nba.png',accent:'#d71920',country:'United States / Canada',league:'National Basketball Association',detail:'Quarter · Clock · Leaders · Box score'},
  mlb:{label:'MLB',icon:'⚾',background:'background-mlb.png',accent:'#d71920',country:'United States / Canada',league:'Major League Baseball',detail:'Inning · Count · Bases · Pitch-by-pitch'},
  nhl:{label:'NHL',icon:'🏒',background:'background-nhl.png',accent:'#1787d3',country:'United States / Canada',league:'National Hockey League',detail:'Period · Shots · Power play · Game centre'},
};
const TABS=[['Overview','▦'],['Live','◉'],['My Team','♜'],['Fixtures','▣'],['Results','✦'],['Standings','▤'],['Teams','♟'],['Players','♙'],['Stats','≋'],['News','▧']];
const LEAGUES={nfl:[['usa','NFL']],nba:[['usa','NBA'],['canada','NBA']],mlb:[['usa','MLB'],['canada','MLB']],nhl:[['usa','NHL'],['canada','NHL']],mls:[['usa','MLS'],['canada','MLS']],more:[['usa','WNBA'],['usa','NCAA'],['canada','CFL']]};
const TEAM_OPTIONS={nfl:{usa:['Arizona Cardinals','Atlanta Falcons','Baltimore Ravens','Buffalo Bills','Chicago Bears','Dallas Cowboys','Green Bay Packers','Kansas City Chiefs','New England Patriots','Philadelphia Eagles','San Francisco 49ers']},nba:{usa:['Boston Celtics','Chicago Bulls','Dallas Mavericks','Golden State Warriors','Los Angeles Lakers','Miami Heat','New York Knicks'],canada:['Toronto Raptors']},mlb:{usa:['Boston Red Sox','Chicago Cubs','Los Angeles Dodgers','New York Yankees','Philadelphia Phillies'],canada:['Toronto Blue Jays']},nhl:{usa:['Boston Bruins','Chicago Blackhawks','New York Rangers','Seattle Kraken','Vegas Golden Knights'],canada:['Calgary Flames','Edmonton Oilers','Montreal Canadiens','Ottawa Senators','Toronto Maple Leafs','Vancouver Canucks']},mls:{usa:['Atlanta United','Inter Miami','LA Galaxy','New York City FC','Seattle Sounders'],canada:['CF Montréal','Toronto FC','Vancouver Whitecaps']},more:{usa:['Choose a league first'],canada:['Choose a league first']}};
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

class UsaSportsHubPanel extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this.sport=localStorage.getItem('usa_sports_hub_selected_sport')||'nfl';this.tab=localStorage.getItem(`usa_sports_hub_${this.sport}_tab`)||'Overview';this.country=localStorage.getItem('usa_sports_hub_country')||'usa';this.team=localStorage.getItem('usa_sports_hub_team')||'';this.selectedLiveGame=localStorage.getItem(`usa_sports_hub_${this.sport}_live_game`)||'';}
  set hass(v){this._hass=v;this.render()} connectedCallback(){this.render()}
  selectSport(s){this.sport=s;this.tab=localStorage.getItem(`usa_sports_hub_${s}_tab`)||'Overview';this.selectedLiveGame=localStorage.getItem(`usa_sports_hub_${s}_live_game`)||'';localStorage.setItem('usa_sports_hub_selected_sport',s);this.render()}
  selectTab(t){this.tab=t;localStorage.setItem(`usa_sports_hub_${this.sport}_tab`,t);this.render()}
  selectCountry(c){this.country=c;this.team='';localStorage.setItem('usa_sports_hub_country',c);localStorage.removeItem('usa_sports_hub_team');this.render()}
  selectTeam(t){this.team=t;localStorage.setItem('usa_sports_hub_team',t)}
  async openLiveGame(id){this.selectedLiveGame=String(id||'');localStorage.setItem(`usa_sports_hub_${this.sport}_live_game`,this.selectedLiveGame);this.render();try{await this._hass?.callService('usa_sports_hub','select_live_match',{fixture_id:this.selectedLiveGame})}catch(err){console.warn('USA Sports Hub game selection failed',err)}}
  closeLiveGame(){this.selectedLiveGame='';localStorage.removeItem(`usa_sports_hub_${this.sport}_live_game`);this.render()} gameLogo(url,name){return url?'<img class="live-team-logo" src="'+esc(url)+'" alt="'+esc(name||'team')+'">':'<span class="live-team-logo fallback">'+esc((name||'?').charAt(0))+'</span>'} liveGameCard(game){const status=game?.is_live?'LIVE':(game?.status_detail||'');const meta=[game?.period_label,game?.clock,game?.venue].filter(Boolean).join(' · ');return '<button class="live-game-card '+(game?.is_live?'active-live':'')+'" data-live-game="'+esc(game?.game_id||'')+'"><div class="live-card-top"><span>'+(game?.is_live?'<i></i> LIVE':esc(status))+'</span><small>'+esc(meta)+'</small></div><div class="live-team-row">'+this.gameLogo(game?.away_logo,game?.away_team)+'<b>'+esc(game?.away_team||'Away')+'</b><strong>'+esc(game?.away_score??'–')+'</strong></div><div class="live-team-row">'+this.gameLogo(game?.home_logo,game?.home_team)+'<b>'+esc(game?.home_team||'Home')+'</b><strong>'+esc(game?.home_score??'–')+'</strong></div><div class="live-card-foot"><span>'+esc(game?.status_detail||'')+'</span><b>OPEN GAME ›</b></div></button>'} livePage(s,items,sensor){
    const games=items('live')||[];
    const totalScore=games.reduce((n,g)=>n+(Number(g.home_score)||0)+(Number(g.away_score)||0),0);
    return '<section class="hero live-hero"><p>USA SPORTS HUB · '+s.label+'</p><h2>'+s.label+' Live Centre</h2><span>'+s.detail+'</span><div class="quick"><b>'+games.length+' LIVE NOW</b><b>'+totalScore+' TOTAL SCORE</b></div></section>'+
      '<section class="live-control"><div><b>ALL LIVE '+s.label+' GAMES</b><span>Click any game to open the full Game Centre</span></div><strong>'+games.length+' LIVE</strong></section>'+
      '<section class="live-games-grid">'+(games.length?games.map(g=>this.liveGameCard(g)).join(''):'<div class="empty-live large">No '+s.label+' games are live right now.</div>')+'</section>';
  }

  pick(obj,keys){for(const key of keys){const value=obj&&obj[key];if(value!==undefined&&value!==null&&value!=='')return value}return ''}
  prettyKey(key){return String(key||'').replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase())}
  compactValue(value){
    if(value===null||value===undefined)return '';
    if(Array.isArray(value))return value.map(x=>typeof x==='object'?(x.name||x.full_name||x.label||x.title||''):x).filter(Boolean).join(', ');
    if(typeof value==='object')return value.name||value.full_name||value.label||value.title||value.value||'';
    return String(value);
  }
  scalarPairs(x){
    if(!x||typeof x!=='object')return [];
    const skip=new Set(['id','api_uri','url','href','link','source_url','source','website','web_url','created_at','updated_at','logos','images','headshot','image','colour_1','colour_2']);
    return Object.entries(x).filter(([key,value])=>!skip.has(key)&&value!==null&&value!==undefined&&value!==''&&typeof value!=='object');
  }
  itemTitle(x){
    const named=this.pick(x,['full_name','first_initial_and_last_name','name','team_name','player_name','title','label','stat_name','category','type']);
    if(named)return named;
    const pairs=this.scalarPairs(x);
    const textPair=pairs.find(([key,value])=>typeof value==='string'&&!['status','clock','game_clock'].includes(key)&&String(value).length>1);
    if(textPair)return this.prettyKey(textPair[0])+': '+String(textPair[1]);
    return pairs.length?this.prettyKey(pairs[0][0]):'Detail';
  }
  itemMeta(x){
    const bits=[];
    for(const key of ['position_abbreviation','jersey_number','team_name','clock','game_clock','segment_string','period','quarter','inning','status']){
      const value=this.compactValue(x&&x[key]); if(value&&!bits.includes(value))bits.push(value);
    }
    return bits.slice(0,4).join(' · ');
  }
  itemValue(x){
    const direct=this.pick(x,['display_value','value','total','points','passing_yards','rushing_yards','receiving_yards','rebounds','assists','shots','hits','runs','earned_runs','strikeouts','saves','goals','tackles','interceptions','home_runs']);
    if(direct!==''&&direct!==undefined&&direct!==null)return direct;
    const pairs=this.scalarPairs(x).filter(([key])=>!['full_name','first_initial_and_last_name','name','team_name','player_name','title','label','stat_name','category','type','description','play_description','text'].includes(key));
    return pairs.slice(0,3).map(([key,value])=>this.prettyKey(key)+' '+value).join(' · ');
  }
  detailRows(rows,limit){
    return (rows||[]).slice(0,limit||30).map(x=>{
      const pairs=this.scalarPairs(x);
      const title=this.itemTitle(x);
      const meta=this.itemMeta(x);
      const used=new Set(['full_name','first_initial_and_last_name','name','team_name','player_name','title','label','stat_name','category','type','description','play_description','text','position_abbreviation','jersey_number','clock','game_clock','segment_string','period','quarter','inning','status']);
      const chips=pairs.filter(([key])=>!used.has(key)).slice(0,5).map(([key,value])=>'<span class="detail-chip"><small>'+esc(this.prettyKey(key))+'</small><b>'+esc(value)+'</b></span>').join('');
      return '<div class="detail-row rich"><div class="detail-main"><b>'+esc(title)+'</b>'+(meta?'<small>'+esc(meta)+'</small>':'')+'</div>'+(chips?'<div class="detail-chips">'+chips+'</div>':'')+'</div>';
    }).join('');
  }
  infoGrid(obj,limit){
    if(!obj||typeof obj!=='object')return '';
    return Object.entries(obj).filter(([key,value])=>!['api_uri','url','href','link','source_url','source','website','web_url','id','diagrams'].includes(key)&&value!==null&&value!==undefined&&value!==''&&typeof value!=='object').slice(0,limit||16).map(([key,value])=>'<div class="info-cell"><small>'+esc(this.prettyKey(key))+'</small><b>'+esc(value)+'</b></div>').join('');
  }
  sensorData(sensor,name,kind){
    const value=sensor(name)?.attributes?.[name];
    if(value!==undefined&&value!==null)return value;
    return kind==='object'?{}:[];
  }
  sportSituation(selected,box,situations){
    const situation=(situations||[])[0]||box||{};
    if(this.sport==='nfl'){
      const down=this.pick(situation,['down','current_down']);
      const distance=this.pick(situation,['distance','formatted_distance','yards_to_go']);
      const possession=this.pick(situation,['possession','possession_team','yard_line']);
      return '<div class="sport-situation"><b>NFL GAME SITUATION</b><span>'+esc([down?('Down '+down):'',distance?('Distance '+distance):'',possession].filter(Boolean).join(' · ')||'Situation data is loading')+'</span></div>';
    }
    if(this.sport==='mlb'){
      const balls=selected.balls??this.pick(situation,['balls']);
      const strikes=selected.strikes??this.pick(situation,['strikes']);
      const outs=selected.outs??this.pick(situation,['outs']);
      return '<div class="sport-situation"><b>MLB GAME SITUATION</b><span>'+esc('Count '+(balls??0)+'-'+(strikes??0)+' · '+(outs??0)+' outs')+'</span><div class="diamond"><i class="'+(selected.second_base?'on':'')+'"></i><i class="'+(selected.third_base?'on':'')+'"></i><i class="'+(selected.first_base?'on':'')+'"></i></div></div>';
    }
    if(this.sport==='nhl'){
      return '<div class="sport-situation"><b>NHL GAME SITUATION</b><span>'+esc((selected.away_strength??'–')+' v '+(selected.home_strength??'–')+(selected.team_on_power_play?' · POWER PLAY':''))+'</span></div>';
    }
    return '<div class="sport-situation"><b>NBA GAME SITUATION</b><span>'+esc([selected.period_label,selected.clock].filter(Boolean).join(' · ')||'Game data is loading')+'</span></div>';
  }
  mlbPlayerPhoto(player,sizeClass){
    const url=player?.headshot||player?.image||player?.headshot_url||'';
    const name=player?.full_name||player?.player_name||player?.name||'Player';
    return url
      ? '<img class="mlb-player-photo '+esc(sizeClass||'')+'" src="'+esc(url)+'" alt="'+esc(name)+'" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'"><span class="mlb-avatar '+esc(sizeClass||'')+'" style="display:none">'+esc(String(name||'?').charAt(0))+'</span>'
      : '<span class="mlb-avatar '+esc(sizeClass||'')+'">'+esc(String(name||'?').charAt(0))+'</span>';
  }

  mlbGameCentre(s,items,sensor){
    const all=[...(items('live')||[]),...(items('fixtures')||[]),...(items('results')||[])];
    const basic=all.find(g=>String(g.game_id)===String(this.selectedLiveGame))||{};
    const detail=this.sensorData(sensor,'game_detail','object');
    const loaded=String(detail.game_id||'')===String(this.selectedLiveGame);
    const game=loaded?Object.assign({},basic,detail):basic;
    const plays=this.sensorData(sensor,'play_by_play');
    const periods=this.sensorData(sensor,'periods');
    const situations=this.sensorData(sensor,'situations');
    const players=this.sensorData(sensor,'players');
    const lineups=this.sensorData(sensor,'lineups');
    const scoring=this.sensorData(sensor,'scoring');
    const stats=this.sensorData(sensor,'statistics');
    const standings=this.sensorData(sensor,'standings');
    const officials=this.sensorData(sensor,'officials');
    const odds=this.sensorData(sensor,'odds','object');
    const stadium=this.sensorData(sensor,'stadium','object');
    const situation=situations[0]||{};
    const latestPlay=plays.length?plays[plays.length-1]:{};
    const batter=this.pick(situation,['batter'])||this.pick(latestPlay,['batter'])||'';
    const pitcher=this.pick(situation,['pitcher'])||this.pick(latestPlay,['pitcher'])||'';
    const batterCard={full_name:batter,headshot:situation.batter_headshot||''};
    const pitcherCard={full_name:pitcher,headshot:situation.pitcher_headshot||''};
    const inningLabel=this.pick(situation,['inning_ordinal','inning_state'])||game.period_label||'';
    const bases=[
      situation.first_base?'1B':'',
      situation.second_base?'2B':'',
      situation.third_base?'3B':''
    ].filter(Boolean).join(' · ')||'Bases empty';

    const validInnings=periods.filter(x=>x&&x.inning&&(
      x.away_runs!==undefined||x.home_runs!==undefined||x.away_hits!==undefined||x.home_hits!==undefined
    ));
    const status=game.is_live?'LIVE':(game.is_final?'FINAL':'GAME CENTRE');

    const inningsHeads=validInnings.map(x=>'<th>'+esc(x.inning)+'</th>').join('');
    const awayCells=validInnings.map(x=>'<td>'+esc(x.away_runs??'–')+'</td>').join('');
    const homeCells=validInnings.map(x=>'<td>'+esc(x.home_runs??'–')+'</td>').join('');
    const awayTotals={
      r:game.away_score??validInnings.reduce((n,x)=>n+(Number(x.away_runs)||0),0),
      h:validInnings.reduce((n,x)=>n+(Number(x.away_hits)||0),0),
      e:validInnings.reduce((n,x)=>n+(Number(x.away_errors)||0),0)
    };
    const homeTotals={
      r:game.home_score??validInnings.reduce((n,x)=>n+(Number(x.home_runs)||0),0),
      h:validInnings.reduce((n,x)=>n+(Number(x.home_hits)||0),0),
      e:validInnings.reduce((n,x)=>n+(Number(x.home_errors)||0),0)
    };

    const lastPlayText=this.pick(latestPlay,['description','event','text'])||'No recent play available.';
    const lastPlayMeta=[
      latestPlay.half_inning,
      latestPlay.inning&&(''+latestPlay.inning),
      batter&&('Batter: '+batter),
      pitcher&&('Pitcher: '+pitcher)
    ].filter(Boolean).join(' · ');

    const statValue=(row,key)=>row&&row[key]!==undefined?row[key]:'–';
    const battingStats=stats.filter(x=>String(x.group||'').toLowerCase()==='batting');
    const pitchingStats=stats.filter(x=>String(x.group||'').toLowerCase()==='pitching');
    const battingRows=battingStats.filter(x=>x.full_name).slice(0,12).map(x=>
      '<div class="mlb-leader-row">'+this.mlbPlayerPhoto(x,'leader')+'<div class="mlb-leader-name"><b>'+esc(x.full_name)+'</b><small>'+esc([x.team_name,x.position_abbreviation].filter(Boolean).join(' · '))+'</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'avg')??statValue(x,'batting_average'))+'</b><small>AVG</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'obp')??statValue(x,'on_base_percentage'))+'</b><small>OBP</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'runs')??statValue(x,'r'))+'</b><small>R</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'homeRuns')??statValue(x,'home_runs'))+'</b><small>HR</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'rbi'))+'</b><small>RBI</small></div></div>'
    ).join('');

    const pitchingRows=pitchingStats.filter(x=>x.full_name).slice(0,8).map(x=>
      '<div class="mlb-leader-row">'+this.mlbPlayerPhoto(x,'leader')+'<div class="mlb-leader-name"><b>'+esc(x.full_name)+'</b><small>'+esc([x.team_name,x.position_abbreviation].filter(Boolean).join(' · '))+'</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'inningsPitched')??statValue(x,'innings_pitched'))+'</b><small>IP</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'hits'))+'</b><small>H</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'runs'))+'</b><small>R</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'earnedRuns')??statValue(x,'earned_runs'))+'</b><small>ER</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'strikeOuts')??statValue(x,'strikeouts'))+'</b><small>K</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'baseOnBalls')??statValue(x,'walks'))+'</b><small>BB</small></div>'+
      '<div class="mlb-mini-stat"><b>'+esc(statValue(x,'era'))+'</b><small>ERA</small></div></div>'
    ).join('');

    // Scoring-play rows from theScore often contain the play sentence but no
    // player object. Match that sentence back to the loaded roster so those
    // cards receive the same portrait as the lineup.
    const roster=[...lineups,...players].filter(x=>x&&typeof x==='object');
    const scoringPerson=row=>{
      const rowId=String(row?.id||row?.player_id||'');
      const byId=rowId&&roster.find(person=>String(person?.id||person?.player_id||'')===rowId);
      if(byId)return {...row,...byId,player_name:row.player_name||byId.full_name||byId.name||''};
      const text=String(row?.player_name||row?.description||row?.event||'').toLowerCase();
      const byName=roster
        .map(person=>({person,name:String(person?.full_name||person?.name||'').trim()}))
        .filter(item=>item.name.length>2&&text.includes(item.name.toLowerCase()))
        .sort((a,b)=>b.name.length-a.name.length)[0]?.person;
      return byName?{...row,...byName,player_name:row.player_name||byName.full_name||byName.name||''}:row;
    };
    const scoreSummary=scoring.slice(0,40).map(x=>{
      const person=scoringPerson(x);
      const inning=[x.half_inning,x.inning&&(''+x.inning)].filter(Boolean).join(' ')||'Scoring play';
      const text=this.pick(x,['description','event','text'])||'Scoring play';
      return '<div class="mlb-score-event"><div class="mlb-score-inning">'+esc(inning)+'</div><div class="mlb-score-event-body with-photo">'+this.mlbPlayerPhoto(person,'score')+'<div><b>'+esc(person.player_name||'')+'</b><span>'+esc(text)+'</span></div></div></div>';
    }).join('');

    const cleanPlayers=(lineups.length?lineups:players).filter(x=>{
      if(!x||typeof x!=='object')return false;
      const n=String(this.pick(x,['full_name','first_initial_and_last_name','player_name','name'])||'').toLowerCase();
      if(!n)return false;
      if(n==='mlb baseball'||n===String(game.home_team||'').toLowerCase()||n===String(game.away_team||'').toLowerCase())return false;
      return Boolean(this.pick(x,['position_abbreviation','position_name','jersey_number','batting_spot','batting_order']));
    });
    const lineupRows=cleanPlayers.slice(0,26).map(x=>
      '<div class="mlb-lineup-row">'+
        (x.batting_spot?'<span class="bat-order">'+esc(x.batting_spot)+'</span>':'')+
        this.mlbPlayerPhoto(x,'lineup')+
        '<div><b>'+esc(this.pick(x,['full_name','name'])||'Player')+'</b><small>'+esc([this.pick(x,['position_abbreviation','position_name']),this.pick(x,['jersey_number'])&&('#'+this.pick(x,['jersey_number'])),x.team_name].filter(Boolean).join(' · '))+'</small></div>'+
      '</div>'
    ).join('');

    const awayStanding=standings.find(x=>x.team===game.away_team)||{};
    const homeStanding=standings.find(x=>x.team===game.home_team)||{};
    const compareRow=(label,a,b)=>'<div class="mlb-compare-row"><b>'+esc(a||'–')+'</b><span>'+label+'</span><b>'+esc(b||'–')+'</b></div>';
    const comparison=
      compareRow('Record',awayStanding.record,homeStanding.record)+
      compareRow('Away/Home',awayStanding.away_record,homeStanding.home_record)+
      compareRow('Last 10',awayStanding.last_ten,homeStanding.last_ten)+
      compareRow('Streak',awayStanding.streak,homeStanding.streak);

    const officialText=officials.map(x=>[x.official_type,x.name].filter(Boolean).join(' - ')).filter(Boolean).join(', ');
    const broadcast=(game.broadcasts||[]).join(', ');
    const venue=[stadium.name||game.venue,stadium.city||game.location,stadium.state].filter(Boolean).join(' · ');
    const oddsText=[
      odds.line,
      odds.over_under&&('O/U '+odds.over_under)
    ].filter(Boolean).join(' · ');

    return '<section class="mlb-centre reference-style">'+
      '<div class="game-centre-top"><button class="live-back" data-live-close>← BACK</button><span class="game-status '+(game.is_live?'live':'')+'">'+(game.is_live?'<i></i> ':'')+status+'</span><small>'+(loaded?'GAME DATA LIVE':'LOADING GAME DATA…')+'</small></div>'+
      '<div class="mlb-reference-grid">'+
        '<main class="mlb-main-column">'+
          '<section class="mlb-matchup-bar"><span>'+esc(inningLabel||game.status_detail||'Game')+'</span><span>◆ '+esc((situation.balls??0)+'-'+(situation.strikes??0)+' · '+(situation.outs??0)+' out'+((situation.outs??0)===1?'':'s'))+'</span></section>'+
          '<section class="mlb-matchup">'+
            '<div class="mlb-match-team">'+this.gameLogo(game.away_logo,game.away_team)+'<div><h2>'+esc(game.away_team||'Away')+'</h2><small>'+esc(awayStanding.record||'')+'</small></div><strong>'+esc(game.away_score??'–')+'</strong></div>'+
            '<div class="mlb-match-team">'+this.gameLogo(game.home_logo,game.home_team)+'<div><h2>'+esc(game.home_team||'Home')+'</h2><small>'+esc(homeStanding.record||'')+'</small></div><strong>'+esc(game.home_score??'–')+'</strong></div>'+
          '</section>'+
          '<section class="mlb-section"><h3>Last Play</h3><div class="mlb-last-play"><b>'+esc(lastPlayText)+'</b>'+(lastPlayMeta?'<small>'+esc(lastPlayMeta)+'</small>':'')+'</div></section>'+
          (validInnings.length?'<section class="mlb-section"><h3>Scoring</h3><div class="mlb-table-wrap"><table class="mlb-linescore"><thead><tr><th></th>'+inningsHeads+'<th>R</th><th>H</th><th>E</th></tr></thead><tbody><tr><th>'+esc(game.away_abbreviation||'AWAY')+'</th>'+awayCells+'<td class="total">'+esc(awayTotals.r)+'</td><td>'+esc(awayTotals.h)+'</td><td>'+esc(awayTotals.e)+'</td></tr><tr><th>'+esc(game.home_abbreviation||'HOME')+'</th>'+homeCells+'<td class="total">'+esc(homeTotals.r)+'</td><td>'+esc(homeTotals.h)+'</td><td>'+esc(homeTotals.e)+'</td></tr></tbody></table></div></section>':'')+
          (pitchingRows?'<section class="mlb-section"><h3>Pitching</h3>'+pitchingRows+'</section>':'')+
          (battingRows?'<section class="mlb-section"><h3>Batting</h3>'+battingRows+'</section>':'')+
          (scoreSummary?'<section class="mlb-section"><h3>Scoring Summary</h3>'+scoreSummary+'</section>':'')+
          (lineupRows?'<section class="mlb-section"><h3>Lineups</h3><div class="mlb-lineup-grid">'+lineupRows+'</div></section>':'')+
        '</main>'+
        '<aside class="mlb-side-column">'+
          '<section class="mlb-side-card"><h3>Game Details</h3>'+
            (venue?'<div><b>'+esc(stadium.name||game.venue||'Venue')+'</b><span>'+esc([stadium.city||game.location,stadium.state].filter(Boolean).join(', '))+'</span></div>':'')+
            (broadcast?'<div><b>Watch on</b><span>'+esc(broadcast)+'</span></div>':'')+
            (officialText?'<div><b>Umpires</b><span>'+esc(officialText)+'</span></div>':'')+
            (oddsText?'<div><b>Closing Odds</b><span>'+esc(oddsText)+'</span></div>':'')+
          '</section>'+
          '<section class="mlb-side-card"><h3>Current At Bat</h3><div class="mlb-atbat-person">'+this.mlbPlayerPhoto(batterCard,'atbat')+'<div><b>'+esc(batter||'—')+'</b><span>Batter</span></div></div>'+(pitcher?'<div class="mlb-atbat-person">'+this.mlbPlayerPhoto(pitcherCard,'atbat')+'<div><b>'+esc(pitcher)+'</b><span>Pitcher</span></div></div>':'')+'<div><b>'+esc(bases)+'</b><span>'+esc((situation.balls??0)+'-'+(situation.strikes??0)+' · '+(situation.outs??0)+' outs')+'</span></div></section>'+
          '<section class="mlb-side-card"><h3>Team Comparison</h3><div class="mlb-compare-head"><b>'+esc(game.away_abbreviation||'AWAY')+'</b><b>'+esc(game.home_abbreviation||'HOME')+'</b></div>'+comparison+'</section>'+
        '</aside>'+
      '</div>'+
    '</section>';
  }

  gameCentre(s,items,sensor){
    if(this.sport==='mlb')return this.mlbGameCentre(s,items,sensor);
    const all=[...(items('live')||[]),...(items('fixtures')||[]),...(items('results')||[])];
    const basic=all.find(g=>String(g.game_id)===String(this.selectedLiveGame))||{};
    const detail=this.sensorData(sensor,'game_detail','object');
    const loaded=String(detail.game_id||'')===String(this.selectedLiveGame);
    const selected=loaded?Object.assign({},basic,detail):basic;
    const box=this.sensorData(sensor,'box_score','object');
    const plays=this.sensorData(sensor,'play_by_play');
    const stats=this.sensorData(sensor,'statistics');
    const drives=this.sensorData(sensor,'drives');
    const scoring=this.sensorData(sensor,'scoring');
    const players=this.sensorData(sensor,'players');
    const lineups=this.sensorData(sensor,'lineups');
    const injuries=this.sensorData(sensor,'injuries');
    const leaders=this.sensorData(sensor,'leaders');
    const periods=this.sensorData(sensor,'periods');
    const officials=this.sensorData(sensor,'officials');
    const situations=this.sensorData(sensor,'situations');
    const odds=this.sensorData(sensor,'odds','object');
    const stadium=this.sensorData(sensor,'stadium','object');
    const ticker=this.sensorData(sensor,'ticker');
    const status=selected.is_live?'LIVE':(selected.is_final?'FINAL':'GAME CENTRE');
    const metric=(label,value,sub)=>'<article><small>'+label+'</small><b>'+esc(value)+'</b><span>'+esc(sub||'')+'</span></article>';
    const metrics=[
      metric('PLAY BY PLAY',plays.length,'events'),
      metric('STATISTICS',stats.length,'records'),
      metric('PLAYERS',players.length,'loaded'),
      metric('LINEUPS',lineups.length,'records'),
      metric('SCORING',scoring.length,'events'),
      metric('INJURIES',injuries.length,'records'),
      metric('LEADERS',leaders.length,'records')
    ];
    if(this.sport==='nfl')metrics.push(metric('DRIVES',drives.length,'possessions'));
    const section=(title,body,count)=>'<article class="game-section"><header><b>'+title+'</b>'+(count!==undefined?'<span>'+esc(count)+'</span>':'')+'</header><div class="game-section-body">'+body+'</div></article>';
    const lineupRows=this.detailRows(lineups.length?lineups:players,70)||'<div class="empty-live">No lineup/player details supplied for this game yet.</div>';
    const statRows=this.detailRows(stats,100)||'<div class="empty-live">No detailed statistics supplied yet.</div>';
    const leaderRows=this.detailRows(leaders,40)||'<div class="empty-live">No leaders supplied yet.</div>';
    const scoringRows=this.detailRows(scoring,60)||'<div class="empty-live">No scoring-event detail supplied yet.</div>';
    const injuryRows=this.detailRows(injuries,40)||'<div class="empty-live">No injury information supplied for this game.</div>';
    const officialRows=this.detailRows(officials,30)||'<div class="empty-live">No officials data supplied.</div>';
    const periodRows=this.detailRows(periods,50)||'<div class="empty-live">No period-by-period detail supplied yet.</div>';
    const playRows=plays.slice(-120).reverse().map(p=>'<div class="play-row"><b>'+esc(this.pick(p,['clock','game_clock','segment_string','period','inning'])||'')+'</b><span>'+esc(this.pick(p,['description','text','play_description','detail','event_description'])||this.itemTitle(p))+'</span></div>').join('')||'<div class="empty-live">No play-by-play supplied yet.</div>';
    const driveRows=this.detailRows(drives,40)||'<div class="empty-live">No drive data supplied yet.</div>';
    const venueInfo=this.infoGrid(Object.assign({},selected.stadium_details||{},stadium),14)||'<div class="empty-live">No venue details supplied.</div>';
    const oddsInfo=this.infoGrid(odds,12)||'<div class="empty-live">No odds data supplied.</div>';
    const boxInfo=this.infoGrid(box,20)||'<div class="empty-live">No compact box-score fields supplied.</div>';
    let sportFeature='';
    if(this.sport==='nfl')sportFeature=section('DRIVES & POSSESSIONS',driveRows,drives.length);
    if(this.sport==='nba')sportFeature=section('QUARTERS / PERIODS',periodRows,periods.length);
    if(this.sport==='mlb')sportFeature=section('INNINGS / LINE SCORE',periodRows,periods.length);
    if(this.sport==='nhl')sportFeature=section('PERIODS / GAME FLOW',periodRows,periods.length);
    return '<section class="game-centre">'+
      '<div class="game-centre-top"><button class="live-back" data-live-close>← BACK</button><span class="game-status '+(selected.is_live?'live':'')+'">'+(selected.is_live?'<i></i> ':'')+status+'</span><small>'+(loaded?'FULL GAME DATA LOADED':'LOADING FULL GAME DATA…')+'</small></div>'+
      '<div class="game-scoreboard"><div class="team-side">'+this.gameLogo(selected.away_logo,selected.away_team)+'<h2>'+esc(selected.away_team||'Away')+'</h2><small>'+esc(selected.away_abbreviation||'')+'</small></div><div class="score-core"><span>'+esc([selected.period_label,selected.clock].filter(Boolean).join(' · '))+'</span><strong>'+esc(selected.away_score??'–')+' <i>–</i> '+esc(selected.home_score??'–')+'</strong><small>'+esc(selected.status_detail||'')+'</small></div><div class="team-side">'+this.gameLogo(selected.home_logo,selected.home_team)+'<h2>'+esc(selected.home_team||'Home')+'</h2><small>'+esc(selected.home_abbreviation||'')+'</small></div></div>'+
      '<div class="venue-strip">'+esc([selected.venue,selected.location,(selected.broadcasts||[]).join(', ')].filter(Boolean).join(' · '))+'</div>'+
      this.sportSituation(selected,box,situations)+
      '<div class="game-metrics">'+metrics.join('')+'</div>'+
      '<div class="game-section-grid">'+
        section('LIVE PLAY-BY-PLAY',playRows,plays.length)+
        section('TEAM / PLAYER STATISTICS',statRows,stats.length)+
        sportFeature+
        section('SCORING SUMMARY',scoringRows,scoring.length)+
        section('LINEUPS & PLAYERS',lineupRows,lineups.length||players.length)+
        section('GAME LEADERS',leaderRows,leaders.length)+
        section('INJURIES',injuryRows,injuries.length)+
        section('OFFICIALS',officialRows,officials.length)+
        section('BOX SCORE DETAILS','<div class="info-grid">'+boxInfo+'</div>')+
        section('VENUE','<div class="info-grid">'+venueInfo+'</div>')+
        section('ODDS','<div class="info-grid">'+oddsInfo+'</div>')+
        section('LIVE TICKER',this.detailRows(ticker,30)||'<div class="empty-live">No ticker items supplied.</div>',ticker.length)+
      '</div></section>';
  }

  sportOverviewExtras(items,sensor){
    const stats=this.sensorData(sensor,'statistics'),players=this.sensorData(sensor,'players'),lineups=this.sensorData(sensor,'lineups'),injuries=this.sensorData(sensor,'injuries'),leaders=this.sensorData(sensor,'leaders'),periods=this.sensorData(sensor,'periods'),drives=this.sensorData(sensor,'drives'),scoring=this.sensorData(sensor,'scoring'),plays=this.sensorData(sensor,'play_by_play');
    const card=(title,value,sub)=>'<article><small>'+title+'</small><b>'+esc(value)+'</b><span>'+esc(sub)+'</span></article>';
    if(this.sport==='nfl')return card('DRIVES',drives.length,'possessions')+card('PLAY BY PLAY',plays.length,'plays')+card('LEADERS',leaders.length,'leaders')+card('INJURIES',injuries.length,'records');
    if(this.sport==='nba')return card('PLAYER STATS',stats.length,'records')+card('LINEUPS',lineups.length,'players')+card('LEADERS',leaders.length,'leaders')+card('PERIODS',periods.length,'quarters');
    if(this.sport==='mlb')return card('LINEUPS',lineups.length,'batting records')+card('PLAYERS',players.length,'loaded')+card('SCORING',scoring.length,'events')+card('INNINGS',periods.length,'records');
    return card('SCORING',scoring.length,'events')+card('PLAYER STATS',stats.length,'records')+card('LINEUPS',lineups.length,'records')+card('PERIODS',periods.length,'records');
  }

  dataPage(s,tab,items,sensor,entity,score){
    const fixtures=items('fixtures'),results=items('results'),live=items('live'),standings=items('standings'),teams=entity?.attributes?.teams||[],players=items('players'),stats=items('statistics'),news=items('news'),scoring=items('scoring'),drives=items('drives'),lineups=items('lineups'),injuries=items('injuries'),leaders=items('leaders'),periods=items('periods'),officials=items('officials'),situations=items('situations'),ticker=items('ticker');
    const box=this.sensorData(sensor,'box_score','object'),odds=this.sensorData(sensor,'odds','object'),stadium=this.sensorData(sensor,'stadium','object');
    if(tab==='Fixtures'||tab==='Results'){
      const games=tab==='Fixtures'?fixtures:results;
      const desc=tab==='Fixtures'?'Upcoming schedule. Every game opens into the full Game Centre.':'Completed games with final scores and full game detail.';
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>'+tab+'</h2><span>'+desc+'</span><div class="schedule-grid">'+(games.length?games.slice(0,80).map(g=>this.liveGameCard(g)).join(''):'<div class="empty-live large">No '+tab.toLowerCase()+' available.</div>')+'</div></section>';
    }
    if(tab==='Standings'){
      const head=this.sport==='mlb'?'<span>GB</span><span>DIFF</span>':this.sport==='nhl'?'<span>PTS</span><span>DIFF</span>':'<span>REC</span><span>SEED</span>';
      const rows=standings.map((x,i)=>{
        const a=this.sport==='mlb'?(x.games_back??'–'):this.sport==='nhl'?(x.points??'–'):(x.record||'–');
        const b=this.sport==='mlb'?(x.runs_differential??'–'):this.sport==='nhl'?(x.goal_differential??'–'):(x.playoff_seed??'–');
        const extra=[x.conference,x.division,x.streak,x.last_ten].filter(Boolean).join(' · ');
        return '<div class="standings-row"><strong>'+esc(x.rank||x.division_rank||i+1)+'</strong>'+this.gameLogo(x.logo,x.team)+'<div><b>'+esc(x.team||'Team')+'</b><small>'+esc(extra)+'</small></div><span>'+esc(a)+'</span><span>'+esc(b)+'</span></div>';
      }).join('');
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>Standings</h2><span>League table with sport-specific record, seed, points and differential data.</span><div class="standings-table"><div class="standings-head"><span>#</span><span></span><span>TEAM</span>'+head+'</div>'+(rows||'<div class="empty-live large">No standings available.</div>')+'</div></section>';
    }
    if(tab==='Teams'){
      const rows=teams.map(x=>'<article class="team-card">'+this.gameLogo(x.logo,x.name)+'<div><h3>'+esc(x.name||'Team')+'</h3><p>'+esc([x.abbreviation,x.location,x.conference,x.division].filter(Boolean).join(' · '))+'</p></div><span>'+esc((x.country||'').toUpperCase())+'</span></article>').join('');
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>Teams</h2><span>'+teams.length+' teams available from the current league feed.</span><div class="teams-grid">'+(rows||'<div class="empty-live large">No team data available.</div>')+'</div></section>';
    }
    if(tab==='Players'){
      const source=players.length?players:lineups;
      const rows=source.slice(0,140).map(x=>'<article class="player-card">'+this.gameLogo(x.headshot||x.image,x.full_name||x.name)+'<div><h3>'+esc(x.full_name||x.name||x.first_initial_and_last_name||'Player')+'</h3><p>'+esc([x.position_abbreviation,x.jersey_number,x.team_name].filter(Boolean).join(' · '))+'</p><small>'+esc(this.itemValue(x))+'</small></div></article>').join('');
      const summary='<div class="stat-summary"><article><small>PLAYERS</small><b>'+players.length+'</b></article><article><small>LINEUPS</small><b>'+lineups.length+'</b></article><article><small>LEADERS</small><b>'+leaders.length+'</b></article><article><small>INJURIES</small><b>'+injuries.length+'</b></article></div>';
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>Players</h2><span>Players, starters, game leaders and injury information from the currently loaded game.</span>'+summary+'<div class="players-grid">'+(rows||'<div class="empty-live large">Open a game to load player and lineup data.</div>')+'</div></section>';
    }
    if(tab==='Stats'){
      const metricCards='<article><small>STAT RECORDS</small><b>'+stats.length+'</b></article><article><small>SCORING</small><b>'+scoring.length+'</b></article><article><small>PERIODS</small><b>'+periods.length+'</b></article><article><small>LEADERS</small><b>'+leaders.length+'</b></article><article><small>SITUATIONS</small><b>'+situations.length+'</b></article>'+(this.sport==='nfl'?'<article><small>DRIVES</small><b>'+drives.length+'</b></article>':'');
      let sportBlock='';
      if(this.sport==='nfl')sportBlock='<h3>NFL Drives & Game Flow</h3>'+this.detailRows(drives,50);
      if(this.sport==='nba')sportBlock='<h3>NBA Quarters & Leaders</h3>'+this.detailRows(periods,50)+this.detailRows(leaders,30);
      if(this.sport==='mlb')sportBlock='<h3>MLB Innings & Situations</h3>'+this.detailRows(periods,50)+this.detailRows(situations,30);
      if(this.sport==='nhl')sportBlock='<h3>NHL Periods & Scoring</h3>'+this.detailRows(periods,50)+this.detailRows(scoring,40);
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>Statistics</h2><span>Sport-specific statistics from every detail sensor currently available.</span><div class="stat-summary">'+metricCards+'</div><div class="stats-showcase"><article><header>STATISTICS</header>'+((this.detailRows(stats,120))||'<div class="empty-live">No statistics loaded.</div>')+'</article><article><header>SPORT DETAIL</header>'+(sportBlock||'<div class="empty-live">Open a game to load detail.</div>')+'</article><article><header>BOX SCORE</header><div class="info-grid">'+(this.infoGrid(box,30)||'<div class="empty-live">No box score fields loaded.</div>')+'</div></article><article><header>ODDS</header><div class="info-grid">'+(this.infoGrid(odds,20)||'<div class="empty-live">No odds available.</div>')+'</div></article><article><header>STADIUM</header><div class="info-grid">'+(this.infoGrid(stadium,20)||'<div class="empty-live">No stadium data available.</div>')+'</div></article><article><header>OFFICIALS</header>'+((this.detailRows(officials,30))||'<div class="empty-live">No officials data available.</div>')+'</article></div></section>';
    }
    if(tab==='News'){
      const cards=news.map(x=>'<article class="news-card"><small>'+esc(x.kind||'UPDATE')+'</small><h3>'+esc(x.title||'News')+'</h3><p>'+esc(x.summary||'')+'</p></article>').join('');
      const tickerRows=this.detailRows(ticker,30);
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>News & Game Reports</h2><span>Previews, recaps and live ticker information from the sport feed.</span><div class="news-grid">'+(cards||'<div class="empty-live large">No current news or reports available.</div>')+'</div>'+(tickerRows?'<div class="ticker-panel"><h3>Live ticker</h3>'+tickerRows+'</div>':'')+'</section>';
    }
    if(tab==='My Team'){
      const name=this.team;
      const all=[...live,...fixtures,...results].filter(g=>!name||g.home_team===name||g.away_team===name);
      const teamInfo=teams.find(x=>x.name===name);
      const standing=standings.find(x=>x.team===name);
      const head=name?'<div class="my-team-head">'+this.gameLogo(teamInfo?.logo,name)+'<div><h3>'+esc(name)+'</h3><span>'+esc([teamInfo?.conference,teamInfo?.division,standing?.record,standing?.formatted_rank].filter(Boolean).join(' · '))+'</span></div></div>':'';
      return '<section class="page data-page"><p>USA SPORTS HUB · '+s.label+'</p><h2>My Team</h2><span>Team schedule, results and current standing in one place.</span>'+head+(name?'<div class="schedule-grid">'+(all.slice(0,30).map(g=>this.liveGameCard(g)).join('')||'<div class="empty-live large">No games loaded for this team.</div>')+'</div>':'<div class="empty-live large">Choose a team from the selector at the top of the dashboard.</div>')+'</section>';
    }
    return '<section class="page"><h2>'+esc(tab)+'</h2><div class="empty-live large">No data available.</div></section>';
  }

  render(){const s=SPORTS[this.sport]||SPORTS.nfl, asset=n=>`/usa_sports_hub/assets/${n}`, time=new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date());
    const sportButtons=Object.entries(SPORTS).map(([id,x])=>`<button class="sport ${id===this.sport?'selected':''}" data-sport="${id}">${x.icon}<span>${x.label}</span></button>`).join(''); const sportLeagues=(LEAGUES[this.sport]||[]).filter(([country])=>country===this.country).map(([,league])=>league); const sensor=section=>this._hass?.states?.[`sensor.usa_sports_hub_${this.sport}_${section}`]; const items=section=>sensor(section)?.attributes?.[section]||[]; const entity=sensor('teams'); const providerTeams=(entity?.attributes?.teams||[]).filter(team=>team.country===this.country).map(team=>team.name); const teams=providerTeams.length?providerTeams:(TEAM_OPTIONS[this.sport]?.[this.country]||[]); const countryLabel={usa:'United States',canada:'Canada',other:'Other'}[this.country]; const fixtures=items('fixtures'),results=items('results'),standings=items('standings'),news=items('news'),live=items('live'); const score=game=>game?`${esc(game.away_team)} ${game.away_score??'–'} · ${game.home_score??'–'} ${esc(game.home_team)}`:'No games available'; const rows=standings.slice(0,3).map((row,index)=>`<li><span>${esc(row.rank||index+1)}</span><b>${esc(row.team)}</b><small>${esc(row.record||'')}</small></li>`).join('')||'<li><b>Standings unavailable</b></li>';
    const nav=TABS.map(([t,i])=>`<button class="nav ${t===this.tab?'selected':''}" data-tab="${t}"><i>${i}</i>${t}${t==='Live'?'<em></em>':''}</button>`).join('');
    const overviewStats={pbp:items('play_by_play').length,stats:items('statistics').length,lineups:items('lineups').length,injuries:items('injuries').length,drives:items('drives').length,scoring:items('scoring').length}; const sportMetric=this.sportOverviewExtras(items,sensor); const livePreview=live.length?`<section class="overview-live"><div class="overview-live-head"><div><b><i></i> LIVE ${s.label}</b><span>Click a game for the full live centre</span></div><button data-tab="Live">VIEW ALL ${live.length}</button></div><div class="overview-live-games">${live.slice(0,3).map(g=>this.liveGameCard(g)).join('')}</div></section>`:''; const overview=`<section class="hero"><p>USA SPORTS HUB · ${s.label}</p><h2>${s.label} Central</h2><span>${s.detail}</span><div class="quick"><b>${live.length} LIVE</b><b>${fixtures.length} FIXTURES</b><b>${standings.length} TEAMS</b><b>${news.length} NEWS</b></div></section><section class="overview-metrics">${sportMetric}</section>${livePreview}<section class="grid"><article class="next"><header><b>▣ &nbsp; NEXT GAME</b><a>UPCOMING</a></header><div class="match"><div><strong>${s.icon}</strong><h3>${esc(fixtures[0]?.away_team||'No fixture')}</h3></div><div class="vs">VS<small>${esc(fixtures[0]?.status_detail||'Schedule unavailable')}</small></div><div><strong>🇺🇸</strong><h3>${esc(fixtures[0]?.home_team||'')}</h3></div></div></article><article class="table"><header><b>▤ &nbsp; ${s.label} STANDINGS</b><a>VIEW ALL</a></header><ol>${rows}</ol></article><article class="card"><header><b>✦ &nbsp; LATEST RESULT</b></header><h3>${score(results[0])}</h3><p>${esc(results[0]?.status_detail||'Results will appear when games finish.')}</p><a>VIEW RESULTS</a></article><article class="card"><header><b>◉ &nbsp; LIVE NOW</b></header><h3>${score(live[0])}</h3><p>${esc(live[0]?.status_detail||'No live games right now.')}</p><a>VIEW LIVE CENTRE</a></article></section>${this.donation(s)}`;
    const page=this.dataPage(s,this.tab,items,sensor,entity,score);
    this.shadowRoot.innerHTML=`<style>
    :host{display:block;color:#f4f8ff;font-family:Inter,system-ui,sans-serif}.shell{min-height:100vh;background:linear-gradient(90deg,#020b19f3 0%,#031123df 43%,#020b19eb 100%),url('${asset(s.background)}') center/cover fixed}.mast{display:flex;align-items:center;gap:20px;padding:22px clamp(18px,5vw,76px);border-bottom:1px solid #1299dd70;background:#031429e9}.brand{display:flex;align-items:center;gap:18px;min-width:310px}.badge{width:108px;height:108px;object-fit:contain;filter:drop-shadow(0 0 16px #168ede80)}.brand h1{font-size:clamp(1.5rem,2.4vw,2.25rem);margin:0;font-weight:950}.brand h1 span{color:#1bb7ff}.brand p{margin:5px 0;color:#c1d1e7;font-size:.85rem}.top{margin-left:auto;display:flex;gap:9px;align-items:center}.update{font-size:.72rem;color:#c3d4e8;white-space:nowrap}.update b{display:block;color:#39d7ff;font-size:.8rem}.select{border:1px solid #ffffff2b;border-radius:10px;background:#031123d9;padding:8px 11px;min-width:130px}.select small{display:block;font-size:.56rem;letter-spacing:.13em;color:#7ea1c9;font-weight:900}.select b{font-size:.75rem}.sports{display:flex;gap:8px;overflow:auto;padding:13px clamp(18px,5vw,76px);background:#06162add;border-bottom:1px solid #1b85c75e}.sport{cursor:pointer;white-space:nowrap;border:1px solid #ffffff2b;background:#ffffff0b;color:#f7faff;border-radius:999px;padding:10px 15px;font-weight:900}.sport span{margin-left:7px}.sport.selected{background:${s.accent};border-color:#fff;box-shadow:0 0 18px ${s.accent}88}.workspace{display:grid;grid-template-columns:180px minmax(0,1fr);max-width:1500px;margin:auto;min-height:680px}.side{display:flex;flex-direction:column;background:#031122d9;border-right:1px solid #168ed15a;padding:16px 8px}.nav{display:flex;position:relative;gap:12px;align-items:center;width:100%;border:0;border-radius:8px;background:transparent;color:#cbd9eb;padding:12px 14px;text-align:left;font-weight:850;cursor:pointer}.nav i{font-style:normal;font-size:1.15rem;width:18px;color:#bcd9f8}.nav.selected{color:#fff;background:linear-gradient(90deg,${s.accent},#087bb850);outline:1px solid #0db9ff}.nav em{width:8px;height:8px;border-radius:50%;background:#ff3151;margin-left:auto}.side-donate{display:block;margin:22px 8px 0;padding:11px 8px;border:1px solid #16b8f4;border-radius:9px;background:#073653;color:#fff;text-align:center;text-decoration:none;font-size:.68rem;font-weight:900}.content{padding:16px;min-width:0}.notice{display:flex;align-items:center;gap:13px;border:1px solid #168ed1a0;border-radius:10px;background:#031429ed;padding:15px 20px;margin-bottom:16px}.notice strong{color:#13afff;font-size:1.35rem}.notice p{margin:0;color:#c8d5e6;font-size:.86rem}.notice b{display:block;color:#fff}.hero,.page{border:1px solid #1c78b690;border-radius:12px;background:linear-gradient(90deg,#04152ce8,#05172bd0),url('${asset(s.background)}') right center/cover;box-shadow:0 10px 30px #0008}.hero{min-height:190px;display:flex;flex-direction:column;justify-content:center;padding:26px 30px}.hero p,.page>p{color:#6dbaff;letter-spacing:.13em;font-size:.76rem;font-weight:950;margin:0}.hero h2,.page h2{font-size:clamp(2rem,4vw,3.25rem);margin:12px 0 5px}.hero>span,.page>span{font-size:.9rem}.quick{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}.quick b{font-size:.72rem;border-radius:8px;background:#17304cdd;padding:10px 12px}.overview-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}.overview-metrics article{border:1px solid #167fc095;border-radius:10px;background:#04152aec;padding:13px}.overview-metrics small{display:block;color:#62c7ff;font-size:.62rem;font-weight:950}.overview-metrics b{display:block;font-size:1.35rem;margin:5px 0}.overview-metrics span{color:#9fb7d0;font-size:.72rem}.overview-live{margin-top:12px;border:1px solid #ff315166;border-radius:10px;background:#160914cc;padding:13px}.overview-live-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.overview-live-head b{color:#ff657a}.overview-live-head i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#ff3151;box-shadow:0 0 10px #ff3151}.overview-live-head span{display:block;color:#aebfd3;font-size:.75rem}.overview-live-head button{border:1px solid #ff315177;border-radius:7px;background:#2a0b16;color:#fff;padding:8px 10px;font-weight:900;cursor:pointer}.overview-live-games{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.grid{display:grid;grid-template-columns:1.3fr 1fr;gap:12px;margin-top:12px}.grid article{border:1px solid #167fc095;border-radius:10px;background:#04152aec;overflow:hidden;min-height:170px}.grid header{display:flex;justify-content:space-between;padding:13px 16px;background:#052545d4;border-bottom:1px solid #178bd078;font-size:.74rem;letter-spacing:.05em}.grid header a,.grid article>a{color:#29d9ff;font-weight:900;font-size:.74rem}.match{display:grid;grid-template-columns:1fr 1fr 1fr;text-align:center;align-items:center;padding:18px}.match strong{font-size:2.5rem}.match h3{font-size:1rem;margin:6px 0}.vs{font-weight:950;color:#22cbff}.vs small{display:block;color:#a9c1dc;font-weight:600;margin-top:7px}.table ol{margin:0;padding:8px 16px;list-style:none}.table li{display:grid;grid-template-columns:30px 1fr 25px;border-bottom:1px solid #ffffff14;padding:10px 0;font-size:.82rem}.table li:last-child{border:0}.table li span{color:#84b9e9}.table li small{text-align:right}.card{padding-bottom:15px}.card h3,.card p,.dots,.card>a{margin-left:16px;margin-right:16px}.card p{color:#bcd0e6;font-size:.85rem}.card>a{display:inline-block;margin-top:11px;text-decoration:none}.dots{display:flex;gap:10px;margin-top:27px}.dots i{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;font-style:normal;background:#13783f;border:1px solid #1ce47b}.dots i:nth-child(2){background:#7d1c2c;border-color:#e03d58}.dots i:nth-child(4){background:#445269;border-color:#8498b5}.donation{display:grid;grid-template-columns:auto 1fr auto;gap:16px;align-items:center;margin-top:12px;padding:20px 24px;border:1px solid #168ed19c;border-radius:10px;background:linear-gradient(90deg,#04152ef5 0%,#04152eea 63%,#04152e99),url('${asset(s.background)}') right center/cover}.donation-icon{font-size:3rem}.donation small{color:#55c5ff;letter-spacing:.1em;font-weight:950}.donation h3{margin:4px 0;font-size:1rem}.donation p{margin:0;color:#d2e1f3;font-size:.84rem}.actions{display:flex;gap:8px}.actions a{background:${s.accent};border-radius:8px;color:white;text-decoration:none;padding:10px 12px;font-weight:900;font-size:.78rem;white-space:nowrap}.page{min-height:440px;padding:34px}.placeholder{margin-top:32px;text-align:center;border:1px dashed #68b7ec8f;border-radius:12px;background:#031020d6;padding:48px 20px}.placeholder strong{font-size:3.5rem}.placeholder h3{margin-bottom:6px}.placeholder p{color:#c3d4e8}.live-hero{border-color:#ff315166}.live-control{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-top:12px;padding:14px 16px;border:1px solid #ff315166;border-radius:10px;background:#1a0913dd}.live-control span{display:block;color:#b9cce3;font-size:.78rem}.live-control strong{color:#ff6075}.live-games-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}.live-game-card{display:block;width:100%;border:1px solid #167fc095;border-radius:10px;background:#05172bed;color:#fff;padding:0;text-align:left;cursor:pointer;overflow:hidden;transition:.15s}.live-game-card:hover{transform:translateY(-1px);border-color:#38c8ff}.live-game-card.active-live{border-color:#ff315199}.live-card-top,.live-card-foot{display:flex;justify-content:space-between;gap:10px;padding:9px 11px;background:#06213dbb;font-size:.7rem}.live-card-top i,.live-detail-banner i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#ff3151;box-shadow:0 0 10px #ff3151}.live-card-foot b{color:#36d3ff}.live-team-row{display:grid;grid-template-columns:38px 1fr auto;align-items:center;gap:8px;padding:9px 11px}.live-team-row strong{font-size:1.4rem}.live-team-logo{width:34px;height:34px;object-fit:contain}.live-team-logo.fallback{display:grid;place-items:center;border-radius:50%;background:#123}.live-detail{border:1px solid #178bd080;border-radius:12px;background:#031020e8;padding:18px}.live-back{border:1px solid #168ed180;border-radius:8px;background:#071c34;color:#fff;padding:9px 12px;cursor:pointer}.live-detail-banner{text-align:center;margin:12px 0;color:#ff6d81;font-weight:950}.live-scoreboard{display:grid;grid-template-columns:1fr .7fr 1fr;gap:16px;align-items:center;text-align:center;padding:20px;border:1px solid #168ed180;border-radius:12px;background:#04172b}.live-scoreboard .live-team-logo{width:88px;height:88px;margin:auto}.live-scoreboard h3{font-size:1rem}.live-score strong{display:block;font-size:3rem}.live-score span{display:block;color:#8fc9ec}.live-venue{text-align:center;color:#abc2da;margin:12px 0}.live-metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px}.live-metric{border:1px solid #167fc080;border-radius:9px;background:#061a30;padding:12px}.live-metric small{display:block;color:#62c7ff;font-size:.62rem;font-weight:950}.live-metric b{display:block;font-size:1.2rem;margin-top:5px}.live-metric span{display:block;color:#a9bdd3;font-size:.72rem}.live-detail-grid{display:grid;grid-template-columns:1.3fr 1fr;gap:12px;margin-top:12px}.live-detail-grid article{border:1px solid #167fc095;border-radius:10px;background:#04152aec;overflow:hidden}.live-detail-grid header{padding:13px 16px;background:#052545d4;border-bottom:1px solid #178bd078;font-weight:900}.live-scroll{max-height:560px;overflow:auto}.play-row,.stat-row{display:grid;grid-template-columns:80px 1fr;gap:10px;padding:10px 12px;border-bottom:1px solid #ffffff12}.play-row b{color:#55c8ff}.stat-row{grid-template-columns:1fr auto}.empty-live{padding:24px;text-align:center;color:#aebfd3}.empty-live.large{grid-column:1/-1;padding:70px 20px}.schedule-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:20px}.standings-table{margin-top:20px;border:1px solid #167fc080;border-radius:10px;overflow:hidden;background:#04152ae8}.standings-head,.standings-row{display:grid;grid-template-columns:42px 42px minmax(180px,1fr) 90px 90px;gap:8px;align-items:center;padding:10px 12px}.standings-head{background:#052545d4;color:#79cef8;font-size:.68rem;font-weight:950}.standings-row{border-top:1px solid #ffffff12}.standings-row .live-team-logo{width:30px;height:30px}.standings-row small{display:block;color:#94abc2}.teams-grid,.players-grid,.news-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:20px}.team-card,.player-card,.news-card{border:1px solid #167fc080;border-radius:10px;background:#04152aec;padding:14px}.team-card,.player-card{display:flex;gap:12px;align-items:center}.team-card .live-team-logo,.player-card .live-team-logo,.my-team-head .live-team-logo{width:52px;height:52px}.team-card h3,.player-card h3,.news-card h3{margin:0 0 5px}.team-card p,.player-card p,.news-card p{margin:0;color:#a9bdd3}.team-card>span{margin-left:auto;color:#72cdf9;font-size:.68rem}.news-card small{color:#66cbff;font-weight:900}.news-card a{display:inline-block;margin-top:12px;color:#38d5ff;font-weight:900;text-decoration:none}.stat-summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin-top:20px}.stat-summary article{border:1px solid #167fc080;border-radius:9px;background:#061a30;padding:12px}.stat-summary small{display:block;color:#62c7ff;font-size:.62rem;font-weight:950}.stat-summary b{display:block;font-size:1.3rem;margin-top:4px}.stats-panel{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.stats-panel>div,.stats-panel pre{max-height:600px;overflow:auto;border:1px solid #167fc080;border-radius:10px;background:#020d19;padding:12px}.stats-panel pre{white-space:pre-wrap;color:#aac5dc;font-size:.72rem}.stat-data-row{display:grid;grid-template-columns:1fr auto;gap:10px;padding:9px;border-bottom:1px solid #ffffff12}.my-team-head{display:flex;align-items:center;gap:14px;margin-top:20px;padding:16px;border:1px solid #167fc080;border-radius:10px;background:#04152aec}.my-team-head h3{margin:0;font-size:1.4rem}.my-team-head span{color:#9db3ca}.game-centre{border:1px solid #178bd080;border-radius:14px;background:linear-gradient(180deg,#031426f7,#020b16f7);padding:18px;box-shadow:0 18px 50px #0009}.game-centre-top{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:12px}.game-centre-top .game-status{justify-self:center;font-weight:950;letter-spacing:.08em}.game-centre-top .game-status.live{color:#ff6377}.game-centre-top i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#ff3151;box-shadow:0 0 12px #ff3151}.game-centre-top small{color:#6fcfff;font-weight:800}.game-scoreboard{display:grid;grid-template-columns:1fr .8fr 1fr;align-items:center;gap:16px;margin-top:14px;padding:28px;border:1px solid #178bd078;border-radius:14px;background:radial-gradient(circle at center,#0b3154 0%,#041529 58%,#020d1a 100%)}.team-side{text-align:center}.team-side .live-team-logo{width:96px;height:96px;margin:auto}.team-side h2{margin:10px 0 2px;font-size:1.25rem}.team-side small{color:#72cef9}.score-core{text-align:center}.score-core>span{color:#71ccfb;font-weight:900}.score-core strong{display:block;font-size:clamp(2.6rem,6vw,5rem);line-height:1;margin:12px 0}.score-core strong i{font-style:normal;color:#5d7690}.score-core small{color:#b4c8dc}.venue-strip{margin:10px 0;text-align:center;color:#a8bed2}.sport-situation{display:flex;align-items:center;justify-content:center;gap:14px;min-height:46px;margin:10px 0;padding:10px 14px;border:1px solid #1b8ed078;border-radius:10px;background:#06223b}.sport-situation b{color:#48c8ff}.sport-situation span{color:#dcecff}.diamond{display:grid;grid-template-columns:12px 12px 12px;grid-template-rows:12px 12px;gap:3px;transform:rotate(45deg);margin-left:14px}.diamond i{width:11px;height:11px;border:1px solid #88a9c4;background:#0b1624}.diamond i.on{background:#ffd34d;box-shadow:0 0 8px #ffd34d}.diamond i:nth-child(1){grid-column:2}.diamond i:nth-child(2){grid-column:1;grid-row:2}.diamond i:nth-child(3){grid-column:3;grid-row:2}.game-metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:12px 0}.game-metrics article{padding:11px;border:1px solid #167fc080;border-radius:9px;background:#061a30}.game-metrics small{display:block;color:#62c7ff;font-size:.61rem;font-weight:950}.game-metrics b{display:block;font-size:1.25rem;margin:3px 0}.game-metrics span{font-size:.68rem;color:#94abc2}.game-section-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.game-section{border:1px solid #167fc080;border-radius:11px;background:#04152aec;overflow:hidden;min-width:0}.game-section>header{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:#062545;border-bottom:1px solid #178bd078}.game-section>header span{display:grid;place-items:center;min-width:28px;height:24px;padding:0 7px;border-radius:999px;background:#0b3e65;color:#79d4ff;font-size:.7rem}.game-section-body{max-height:520px;overflow:auto}.detail-row{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;padding:10px 12px;border-bottom:1px solid #ffffff10}.detail-row:last-child{border-bottom:0}.detail-row small{display:block;color:#8faac3;margin-top:2px}.detail-row strong{color:#71d6ff}.detail-row.rich{grid-template-columns:minmax(150px,1fr) minmax(220px,1.4fr);align-items:start}.detail-main small{display:block}.detail-chips{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px}.detail-chip{min-width:64px;padding:5px 7px;border:1px solid #ffffff12;border-radius:7px;background:#07182a;text-align:right}.detail-chip small{display:block;color:#6dbfe8;font-size:.56rem;text-transform:uppercase}.detail-chip b{display:block;color:#fff;font-size:.75rem;margin-top:1px}.info-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;padding:10px}.info-cell{padding:9px;border:1px solid #ffffff12;border-radius:8px;background:#020d18}.info-cell small{display:block;color:#6fcfff;font-size:.62rem}.info-cell b{display:block;margin-top:3px;word-break:break-word}.stats-showcase{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}.stats-showcase>article{border:1px solid #167fc080;border-radius:10px;background:#04152aec;overflow:hidden}.stats-showcase>article>header{padding:12px 14px;background:#062545;border-bottom:1px solid #178bd078;font-weight:900}.stats-showcase h3{padding:0 12px}.ticker-panel{margin-top:16px;border:1px solid #167fc080;border-radius:10px;background:#04152aec;padding:14px}.mlb-centre{border:1px solid #178bd080;border-radius:14px;background:linear-gradient(180deg,#031426f8,#020a14f8);padding:18px;box-shadow:0 18px 50px #0009}.mlb-score-hero{display:grid;grid-template-columns:1fr .8fr 1fr;align-items:center;gap:20px;margin-top:14px;padding:30px;border:1px solid #178bd078;border-radius:16px;background:radial-gradient(circle at center,#0c3459 0%,#041529 55%,#020d1a 100%)}.mlb-team{text-align:center}.mlb-team .live-team-logo{width:100px;height:100px;margin:auto}.mlb-team h2{margin:10px 0 2px;font-size:1.25rem}.mlb-team small{color:#65cfff}.mlb-score-core{text-align:center}.mlb-score-core>span{display:block;color:#5ed2ff;font-weight:950;text-transform:uppercase}.mlb-score-core strong{display:block;margin:10px 0;font-size:clamp(3rem,6vw,5rem);line-height:1}.mlb-score-core strong i{font-style:normal;color:#58718b}.mlb-score-core small{color:#b9cce0}.mlb-now{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0}.mlb-now>div{padding:13px 14px;border:1px solid #167fc080;border-radius:10px;background:#06213a}.mlb-now small{display:block;color:#53ccff;font-size:.6rem;font-weight:950}.mlb-now b{display:block;margin-top:4px;font-size:1rem}.mlb-now span{display:block;color:#9db5cb;font-size:.72rem;margin-top:2px}.mlb-content-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.mlb-panel{border:1px solid #167fc080;border-radius:11px;background:#04152aec;overflow:hidden}.mlb-panel.wide{margin-bottom:12px}.mlb-panel>header{padding:13px 16px;background:linear-gradient(90deg,#07365a,#05213a);border-bottom:1px solid #178bd078}.mlb-panel>header small{color:#5ed2ff;font-size:.58rem;font-weight:950;letter-spacing:.1em}.mlb-panel>header h3{margin:2px 0 0;font-size:1rem}.mlb-table-wrap{overflow:auto}.mlb-linescore{width:100%;border-collapse:collapse;text-align:center;min-width:680px}.mlb-linescore th,.mlb-linescore td{padding:10px 9px;border-bottom:1px solid #ffffff10}.mlb-linescore thead th{color:#64ccfa;background:#031322;font-size:.7rem}.mlb-linescore tbody th{text-align:left;color:#fff}.mlb-linescore .total{font-weight:950;color:#fff;background:#0a2944}.mlb-scroll{max-height:520px;overflow:auto}.mlb-play{padding:12px 14px;border-bottom:1px solid #ffffff10}.mlb-play-meta{display:flex;justify-content:space-between;color:#5dcfff;font-size:.72rem}.mlb-play p{margin:5px 0;color:#f3f7fb}.mlb-play small{color:#8faac3}.mlb-stat-row{padding:12px 14px;border-bottom:1px solid #ffffff10}.mlb-stat-row>b{display:block;margin-bottom:8px}.mlb-stat-row>div{display:flex;flex-wrap:wrap;gap:7px}.mlb-stat-row span{min-width:90px;padding:7px 8px;border:1px solid #ffffff10;border-radius:7px;background:#06182a}.mlb-stat-row span small{display:block;color:#61c9f7;font-size:.54rem;text-transform:uppercase}.mlb-stat-row span strong{display:block;margin-top:2px}.mlb-summary-row{padding:12px 14px;border-bottom:1px solid #ffffff10}.mlb-summary-row small{display:block;color:#86a4bd;margin-top:3px}.mlb-player-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0}.mlb-player{padding:11px 13px;border-bottom:1px solid #ffffff0d}.mlb-player{display:flex;align-items:center;gap:10px}.bat-order{display:grid;place-items:center;min-width:26px;height:26px;border-radius:50%;background:#0b3d63;color:#6ed5ff;font-weight:950;font-size:.72rem}.mlb-player small{display:block;color:#8faac3;margin-top:2px}.reference-style{background:#01070d}.mlb-reference-grid{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(280px,.95fr);gap:26px;margin-top:14px}.mlb-main-column,.mlb-side-column{min-width:0}.mlb-matchup-bar{display:flex;justify-content:space-between;gap:12px;padding:10px 14px;background:#17202a;color:#c8d1db;font-weight:800}.mlb-matchup{border-bottom:1px solid #243242}.mlb-match-team{display:grid;grid-template-columns:70px 1fr auto;align-items:center;gap:16px;padding:20px 12px}.mlb-match-team+.mlb-match-team{border-top:1px solid #243242}.mlb-match-team .live-team-logo{width:58px;height:58px}.mlb-match-team h2{margin:0;font-size:1.8rem}.mlb-match-team small{display:block;margin-top:3px;color:#9ba9b8}.mlb-match-team>strong{font-size:2.8rem}.mlb-section{margin-top:24px}.mlb-section>h3{margin:0 0 10px;padding:0 10px;font-size:1.45rem}.mlb-last-play{padding:14px;background:#151a20;border-left:3px solid #38a5ff}.mlb-last-play small{display:block;margin-top:5px;color:#94a4b6}.mlb-leader-row{display:grid;grid-template-columns:52px minmax(150px,1fr) repeat(7,minmax(48px,72px));align-items:center;gap:8px;padding:11px 10px;border-bottom:1px solid #172330}.mlb-avatar{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;background:#0a5d63;font-weight:950}.mlb-player-photo{display:block;border-radius:50%;object-fit:cover;background:#0a1722;border:1px solid #264761}.mlb-player-photo.leader{width:44px;height:44px}.mlb-player-photo.score{width:56px;height:56px}.mlb-player-photo.lineup{width:38px;height:38px}.mlb-player-photo.atbat,.mlb-avatar.atbat{width:52px;height:52px}.mlb-atbat-person{display:grid!important;grid-template-columns:58px 1fr;gap:10px;align-items:center}.mlb-score-event-body.with-photo{display:grid;grid-template-columns:60px 1fr;gap:12px;align-items:center}.mlb-score-event-body.with-photo b{display:block}.mlb-score-event-body.with-photo span{display:block;color:#b8c7d6;margin-top:3px}.mlb-leader-name b{display:block}.mlb-leader-name small{display:block;color:#8fa3b8}.mlb-mini-stat{text-align:center}.mlb-mini-stat b{display:block}.mlb-mini-stat small{font-size:.58rem;color:#7e92a6}.mlb-score-event{margin-bottom:2px}.mlb-score-inning{padding:9px 14px;background:#1a2026;color:#aab7c5;font-weight:800}.mlb-score-event-body{padding:12px 14px;border-bottom:1px solid #162330}.mlb-lineup-grid{display:grid;grid-template-columns:1fr 1fr;border:1px solid #162330}.mlb-lineup-row{display:flex;gap:9px;align-items:center;padding:10px 12px;border-bottom:1px solid #162330}.mlb-lineup-row:nth-child(odd){border-right:1px solid #162330}.mlb-lineup-row small{display:block;color:#8fa3b8}.mlb-side-column{position:sticky;top:12px;align-self:start}.mlb-side-card{margin-bottom:18px;padding:16px;border:1px solid #1b2a38;background:#050b11}.mlb-side-card h3{margin:0 0 12px;font-size:1.35rem}.mlb-side-card>div{padding:10px 0;border-top:1px solid #1a2530}.mlb-side-card>div:first-of-type{border-top:0}.mlb-side-card b{display:block}.mlb-side-card span{display:block;color:#9ca9b8;margin-top:2px}.mlb-compare-head{display:grid!important;grid-template-columns:1fr 1fr;text-align:center;background:#151a20}.mlb-compare-row{display:grid!important;grid-template-columns:1fr 1fr 1fr;text-align:center;align-items:center}.mlb-compare-row span{margin:0;color:#9ca9b8}.mlb-compare-row b{font-size:1.05rem}@media(max-width:1000px){.mlb-reference-grid{grid-template-columns:1fr}.mlb-side-column{position:static}.mlb-leader-row{grid-template-columns:44px minmax(130px,1fr) repeat(4,minmax(45px,1fr))}.mlb-leader-row .mlb-mini-stat:nth-last-child(-n+3){display:none}}@media(max-width:650px){.mlb-match-team{grid-template-columns:52px 1fr auto}.mlb-match-team .live-team-logo{width:46px;height:46px}.mlb-match-team h2{font-size:1.2rem}.mlb-match-team>strong{font-size:2rem}.mlb-lineup-grid{grid-template-columns:1fr}.mlb-lineup-row:nth-child(odd){border-right:0}.mlb-leader-row{grid-template-columns:40px 1fr 55px 55px}.mlb-leader-row .mlb-mini-stat:nth-last-child(-n+5){display:none}}@media(max-width:850px){.mlb-content-grid{grid-template-columns:1fr}.mlb-now{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.mlb-score-hero{grid-template-columns:1fr}.mlb-now{grid-template-columns:1fr}.mlb-player-grid{grid-template-columns:1fr}}@media(max-width:1050px){.schedule-grid,.teams-grid,.players-grid,.news-grid{grid-template-columns:repeat(2,1fr)}.stat-summary{grid-template-columns:repeat(3,1fr)}.overview-metrics,.overview-live-games{grid-template-columns:repeat(2,1fr)}.live-games-grid{grid-template-columns:repeat(2,1fr)}.live-metrics{grid-template-columns:repeat(3,1fr)}.top{display:none}.workspace{grid-template-columns:1fr}.side{flex-direction:row;overflow:auto;gap:5px;padding:8px;border-right:0;border-bottom:1px solid #168ed15a}.nav{width:auto;white-space:nowrap}.nav i{display:none}.side-donate{margin:0 0 0 auto;white-space:nowrap}.badge{width:75px;height:75px}}@media(max-width:700px){.schedule-grid,.teams-grid,.players-grid,.news-grid,.stats-panel,.overview-metrics,.overview-live-games,.live-games-grid,.live-detail-grid{grid-template-columns:1fr}.stat-summary{grid-template-columns:repeat(2,1fr)}.standings-head,.standings-row{grid-template-columns:34px 34px 1fr 60px 60px}.live-scoreboard{grid-template-columns:1fr}.live-metrics{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.mast{padding:14px 16px}.badge{width:58px;height:58px}.brand{min-width:0;gap:10px}.brand h1{font-size:1.3rem}.sports{padding:10px 12px}.content{padding:12px}.hero{padding:21px}.donation{grid-template-columns:1fr}.actions{flex-wrap:wrap}}@media(max-width:500px){.grid{display:block}.grid article{margin-bottom:12px}.side-donate{display:none}}
    </style><div class="shell"><header class="mast"><div class="brand"><img class="badge" src="/usa_sports_hub/icon.png" alt="USA Sports Hub"><div><h1>USA <span>SPORTS</span> HUB</h1><p>All your American sports in one place</p></div></div><div class="top"><div class="update"><b>● UP TO DATE</b>Updated just now · ${time}</div><label class="select"><small>COUNTRY</small><select data-country><option value="usa" ${this.country==='usa'?'selected':''}>United States</option><option value="canada" ${this.country==='canada'?'selected':''}>Canada</option><option value="other" ${this.country==='other'?'selected':''}>Other</option></select></label><label class="select"><small>LEAGUE</small><select data-league>${sportLeagues.length?sportLeagues.map(league=>`<option>${league}</option>`).join(''):'<option>No leagues available</option>'}</select></label><label class="select"><small>TEAM</small><select data-team><option value="">All teams</option>${teams.map(team=>`<option ${team===this.team?'selected':''}>${team}</option>`).join('')}</select></label></div></header><nav class="sports">${sportButtons}</nav><div class="workspace"><aside class="side">${nav}<a class="side-donate" href="https://ko-fi.com/ady1984" target="_blank" rel="noopener noreferrer">★ KEEP US IN PLAY</a></aside><main class="content"><section class="notice"><strong>★</strong><p><b>${countryLabel} · ${sportLeagues[0]||'No league'}${this.team?` · ${this.team}`:''}</b>Choose a sport to explore its dedicated dashboard and saved tab layout.</p></section>${this.selectedLiveGame?this.gameCentre(s,items,sensor):(this.tab==='Overview'?overview:(this.tab==='Live'?this.livePage(s,items,sensor):page))}</main></div></div>`;
    this.shadowRoot.querySelectorAll('[data-sport]').forEach(b=>b.addEventListener('click',()=>this.selectSport(b.dataset.sport)));this.shadowRoot.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>this.selectTab(b.dataset.tab)));this.shadowRoot.querySelectorAll('[data-live-game]').forEach(b=>b.addEventListener('click',()=>this.openLiveGame(b.dataset.liveGame)));this.shadowRoot.querySelector('[data-live-close]')?.addEventListener('click',()=>this.closeLiveGame());this.shadowRoot.querySelector('[data-country]')?.addEventListener('change',e=>this.selectCountry(e.target.value));this.shadowRoot.querySelector('[data-team]')?.addEventListener('change',e=>this.selectTeam(e.target.value));
  }
  donation(s){return `<section class="donation"><span class="donation-icon">${s.icon}</span><div><small>SUPPORT ${s.label}</small><h3>Keep USA Sports Hub in play</h3><p>Help support new ${s.label} data, features, and live game coverage.</p></div><div class="actions"><a href="https://ko-fi.com/ady1984" target="_blank" rel="noopener noreferrer">Support via Ko-fi</a><a href="https://paypal.me/graffidoodle" target="_blank" rel="noopener noreferrer">PayPal</a></div></section>`}
}
/* MLB guard: never show a generic roster or 0-0 count as selected-game data. */
UsaSportsHubPanel.prototype.mlbPlayerPhoto=function(player,sizeClass){
  const id=player?.id||player?.player_id||player?.person?.id||'';
  const scoreHeadshot=player?.headshots?.w192xh192||player?.headshots?.large||player?.headshots?.original||'';
  // Route portraits through Home Assistant. This avoids third-party image CSP
  // and referrer issues for official MLB IDs. theScore IDs are different and
  // must use the valid portrait URL supplied with their roster record.
  const url=scoreHeadshot||player?.headshot||player?.image||player?.headshot_url||
    (id?`/api/usa_sports_hub/mlb/headshot/${encodeURIComponent(id)}`:'');
  const name=player?.full_name||player?.player_name||player?.name||'Player';
  return url
    ? '<img class="mlb-player-photo '+esc(sizeClass||'')+'" src="'+esc(url)+'" alt="'+esc(name)+'" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'"><span class="mlb-avatar '+esc(sizeClass||'')+'" style="display:none">'+esc(String(name||'?').charAt(0))+'</span>'
    : '<span class="mlb-avatar '+esc(sizeClass||'')+'">'+esc(String(name||'?').charAt(0))+'</span>';
};
const usaMlbGameCentre=UsaSportsHubPanel.prototype.mlbGameCentre;
UsaSportsHubPanel.prototype.mlbGameCentre=function(s,items,sensor){
  const all=[...(items('live')||[]),...(items('fixtures')||[]),...(items('results')||[])];
  const selected=all.find(game=>String(game.game_id||'')===String(this.selectedLiveGame||''))||{};
  const liveOrFinal=Boolean(selected.is_live||selected.is_final);
  const event=sensor('game_detail')?.attributes?.game_detail||{};
  const detailMatches=String(event.game_id||'')===String(this.selectedLiveGame||'');
  const verified=detailMatches&&Boolean(event.mlb_live_verified);
  const names=new Set([selected.home_team,selected.away_team].filter(Boolean).map(name=>String(name).toLowerCase()));
  const fields=['lineups','players','statistics','situations','play_by_play','scoring','officials','odds','stadium'];
  const safeSensor=name=>{
    const state=sensor(name); if(!state||!fields.includes(name))return state;
    const source=state.attributes?.[name]||[];
    if(!verified){
      const empty=['odds','stadium'].includes(name)?{}:[];
      return {...state,attributes:{...state.attributes,[name]:empty}};
    }
    const allowed=name==='situations'?Boolean(selected.is_live):liveOrFinal;
    if(['odds','stadium'].includes(name))return state;
    const filtered=!allowed||!Array.isArray(source)?[]:
      (name==='situations'||name==='play_by_play'||name==='scoring'||name==='officials'?source:
        source.filter(row=>names.has(String(row?.team_name||'').toLowerCase())));
    return {...state,attributes:{...state.attributes,[name]:filtered}};
  };
  let html=usaMlbGameCentre.call(this,s,items,safeSensor)
    .replace('Bases empty','First pitch pending')
    .replace('0-0 · 0 outs','No live count yet')
    .replace('No recent play available.','Lineups and live play details will appear when the game starts.');
  if(!selected.is_live){
    html=html.replace(/<section class="mlb-side-card"><h3>Current At Bat<\/h3>[\s\S]*?<\/section><section class="mlb-side-card"><h3>Team Comparison/, '<section class="mlb-side-card"><h3>Game Status</h3><div><b>'+esc(selected.is_final?'Final':'Pre-game')+'</b><span>At-bat, bases and count appear only while this game is live.</span></div></section><section class="mlb-side-card"><h3>Team Comparison');
  }
  return html;
};
/* Live card override: place game state and score ahead of secondary metadata. */
UsaSportsHubPanel.prototype.liveGameCard=function(game){
  const isLive=Boolean(game?.is_live), selected=String(game?.game_id||'')===String(this.selectedLiveGame||'');
  const label=isLive?'LIVE UPDATE':(game?.is_final?'FINAL':game?.status_detail||'SCHEDULED');
  const timing=[game?.period_label,game?.clock].filter(Boolean).join(' · ')||game?.status_detail||'Awaiting update';
  return '<button class="live-game-card '+(isLive?'active-live ':'')+(selected?'selected-live':'')+'" data-live-game="'+esc(game?.game_id||'')+'" style="position:relative;overflow:hidden;'+(selected?'box-shadow:0 0 0 2px #35d5ff,0 0 28px #35d5ff55;':'')+'">'+
    '<div class="live-card-top" style="background:'+(isLive?'linear-gradient(90deg,#5c0d22,#250917)':'#06213d')+'"><span style="font-weight:950;letter-spacing:.08em">'+(isLive?'<i></i> ':'')+label+'</span><small style="font-weight:800">'+esc(timing)+'</small></div>'+
    '<div class="live-team-row"><span>'+this.gameLogo(game?.away_logo,game?.away_team)+'</span><b>'+esc(game?.away_team||'Away')+'</b><strong style="font-size:1.75rem">'+esc(game?.away_score??'–')+'</strong></div>'+
    '<div class="live-team-row"><span>'+this.gameLogo(game?.home_logo,game?.home_team)+'</span><b>'+esc(game?.home_team||'Home')+'</b><strong style="font-size:1.75rem">'+esc(game?.home_score??'–')+'</strong></div>'+
    '<div class="live-card-foot"><span>'+esc(game?.venue||game?.status_detail||'')+'</span><b>'+ (selected?'NOW PLAYING':'OPEN GAME ›') +'</b></div></button>';
};
customElements.define('usa-sports-hub-panel',UsaSportsHubPanel);

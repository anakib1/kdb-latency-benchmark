system"l common.q"

times:([]
  time: `timestamp$();
  latency: `timespan$())

pctl:{[x;p] sx:asc x; sx floor p*(count sx)-1}

.upd:{[msg]
  ts: first msg;
  lat: last msg;
  `times upsert (ts; lat);
  if[(count times)=TOTAL_BARS; exit 0;]
  }

printStats:{
  if[count times>0;
    ps: 0.5 0.9 0.99 0.999 0.9999;
    vals: {pctl[times[`latency];x]} each ps;
    {-1 "p", string[(x 0) * 100], ": ", string[(x 1)];} each flip (ps; vals)
    if[x;
        fl: hopen ":../results/results.txt";
        fl "," sv (string THROUGHPUT,vals);
        fl "\n";
        hclose fl;]
  ];
 };


.z.exit: {-1 string count times; save `:../results/times.csv; printStats[1b]; }
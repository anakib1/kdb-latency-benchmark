/ sub.q
h:hopen `:unix://5010
h".u.sub[`;`]"
system"l common.q"
out:{-1 string[.z.P],"::: ",x;}
st:0;

.stTime:0ng;

logger: @[value; "hopen `:unix://5001"; -1]

upd: {
    d: .z.n - y[`time] 0;
    if[logger<>-1; neg[logger](".upd";(.z.P,d));];
    st +: count y;
    if[0=st mod 2000000; show st;];
    if[st >= TOTAL_BARS; out "Elapsed: ",string[.z.P-.stTime],". Rate: ",string[`long$TOTAL_BARS*0D00:00:01%(.z.P-.stTime)]," ts/sec"; exit 0;];
    if[null .stTime; .stTime:.z.P];
    };

.z.exit:{ neg[logger](::); logger""; show st;}
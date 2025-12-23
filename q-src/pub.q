system"l common.q"
INTERVAL:0D00:00:01%THROUGHPUT

out:{-1 string[.z.P],"::: ",x;}

h:hopen `:unix://5010
out "Writing Trades";

ts:.z.n;
do[TOTAL_BARS;
    batch_data:(ts;`$("SYMBOL", string rand 1000); rand 1000000000; rand 100f;rand 100f);
    ts:ts+("j"$INTERVAL);
    neg[h](".u.upd";`trades;batch_data);
    neg[h](::);
    while[.z.n<ts]]

out "Done";
exit 0;
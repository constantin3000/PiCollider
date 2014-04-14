s.waitForBoot{

(
// Dictionary
q = ();
q.current = ();
q.center = ();
q.target = ();
q.current.tab = ();
q.center.tab = ();
q.target.tab = ();


/*
corresponding adc channeels to pot positions
7  5  3

6  4  2
*/
q.oscmap = [
			nil,
			nil,
	[\Pulsar, \amp, "/adc2"],
	[\Pulsar, \reso, "/adc3"],
	[\Pulsar, \pan, "/adc4"],
	[\Pulsar, \form, "/adc5"],
	[\Pulsar, \pulsaret, "/adc6"],
	[\Pulsar, \fund, "/adc7"],
];

/*
q.current.tab.pan.plot
*/
// Functions
q.func = ();

q.func.envSignal = { |num = 8, peak = 1, min = 0, max = 1.0, add = 0.0, curve = \sin|
	var levels;
	levels = {rrand(min, max)}!num;
	levels = levels.add(levels[0]);
	peak ** (add + Env(levels, {1.0.rand}!(num-1), curve).discretize.as(Array));
};

q.func.sineSignal = { |num = 8, randAmp = false, randPhase = false|
	var amps, phases;
	if(randAmp, {
		amps = {1.0.rand}!num;
		},{
		amps = 1/(1..num).scramble;
	});
	if(randPhase, {
		phases =  [0, (2pi/(1..(num-2))).scramble, 0].flat;
	}, {
		phases = 0!num;
	});
	Signal.sineFill(1024, amps, phases);
};

q.func.brownSignal = { |min = -1.0, max = 1.0, step = 0.2|
	Pbrown(min, max, step).asStream.nextN(1024);
};

// Tables
// current
// pulsaret and evnelope
q.current.tab.env = Env.perc.discretize;
q.current.tab.pulsaret = q.func[\sineSignal].value(24, false, true);

//center
// pulsaret and evnelope
q.center.tab.env = Env.perc.discretize;
q.center.tab.pulsaret = q.func[\sineSignal].value(32, false, true);

//target
// pulsaret and evnelope
q.target.tab.env = Env.perc.discretize;
q.target.tab.pulsaret = q.func[\brownSignal].value(-1.0, 1.0, 0.6);
);

s.sync; 0.1.wait;

(
// create buffers
q.current.bufs = q.current.tab.collect({ |val, key| Buffer.sendCollection(s, val, 1) });
q.center.bufs = q.center.tab.collect({ |val, key| Buffer.sendCollection(s, val, 1) });
q.target.bufs = q.target.tab.collect({ |val, key| Buffer.sendCollection(s, val, 1) });
);

s.sync; 0.1.wait;

(
Spec.add(\select, [0, 1]);
Spec.add(\fund, [1, 400, \exp]);
Spec.add(\form, [10, 1000, \exp]);

Spec.add(\pulsaret, \select);
Spec.add(\envret, \select);
Spec.add(\reso, [1/8, 4]);

(
Ndef(\Pulsar, { |fund = 100, form = 200, pulsaret = 0, envret = 0, reso = 1, pan = 0, amp = 0.1|
	var wavebufs, envbufs, impulse, grainDur, rate, pulsars, mix, num = 3;

	wavebufs = q.current.bufs.pulsaret.bufnum;
	envbufs = q.current.bufs.env.bufnum;

	impulse = Impulse.ar(fund);
	grainDur = form.reciprocal;
	rate = form * BufDur.kr(wavebufs);
	pulsars = GrainBuf.ar(2, impulse, grainDur, wavebufs, rate, 0, 4, pan, envbufs, 16) * amp;

				// mix = SelectX.ar(pulsaret * num, pulsars);
	mix = pulsars;
	mix = CombC.ar(mix, 0.2, fund.reciprocal * reso) * 0.1;
	// mix = Ringz.ar(mix, form, fund.reciprocal * reso);
	mix;
}).play;
);

);

s.sync; 0.1.wait;

/*
// is slow
(
OSCdef(\adc, { |msg, time|
	var values;
	// we only look at the data, drop path
	values = msg.keep(-8);
			// values.postln;
			// values = values/4095.0;
	values.do{ |value, i|
				// [value,i].postln;
		if(q.oscmap[i].notNil, {
			var ndef, spec, adc;
			#ndef, spec, adc = q.oscmap[i];
			Ndef(ndef).set(spec, spec.asSpec.map(value));
		});
	};
}, "/adc");
);
*/

(
OSCdef(\adc, { |msg, time|
	var values;
	// we only look at the data, drop path
	values = msg.keep(-8);
	// values.postln;

	values.do{ |value, i|
		// [value,i].postln;
		switch (i,
			2, { Ndef(\Pulsar).set(\amp, \amp.asSpec.map(value)) },
			3, { Ndef(\Pulsar).set(\reso, \reso.asSpec.map(value)) },
			4, { Ndef(\Pulsar).set(\pan, \pan.asSpec.map(value)) },
			5, { Ndef(\Pulsar).set(\form, \form.asSpec.map(value)) },
			6, { Ndef(\Pulsar).set(\pulsaret, \pulsaret.asSpec.map(value)) },
			7, { Ndef(\Pulsar).set(\fund, \fund.asSpec.map(value)) },
		);
	};
}, "/adc");
);

}; //s.doWhenBooted
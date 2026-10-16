B4: supplied-video ended/error recovery controls, not provider-live verification

DefaultOFF PUBLIC_BRICS_RECOVERY_ENABLED=false. Requires the existing public
sample and suppliedvideo wall flag. OFF returns before file/pin/transform work;
existing baseassets/shell/API/headers unchanged, no wrapping. ON fixedhash-checks
basepublicJS and recoveryJS, checks3exact servedcopyseams and appends recovery
module in the existing sameorigin JSasset. No new route/allowlist/provider/API,
no original BRICS engine import or mutation. Existing compulsoryRepublic,
browseronly8extras validation,5seedchecks,private-storage separation and guarded
read-onlyserver API retained. Both publicsample/live builders install only after
existing publicwall. HEAD no read; baseorigin/method/query/CSP guards retained.

Original BRICSdashboard's lightweight ended detection is the fidelity source:
enablejsapi=1 and origin on each embed URL; one listening handshake after each
ownedframe load. B4 improves that source's wildcardtarget/uncheckedorigin to
exact https://www.youtube-nocookie.com and currentownediframe contentWindow.
Listening includes a distinct frameID. No fullproviderAPI script, timer,
availabilitylookup, poll or automaticretry. At most6defaultiframes as before;
customextras still clickload. Provideriframe loads are the existing external
YouTube interaction, not a privacy-free operation. Gates remainOFF in deployment.

BoundedJSONstring<=4096; infoDelivery.playerState===0 or onStateChange.info===0
means this player reported ended. onError integer2/5/100/101/150 means a reported
playbackerror, not confirmed offline/liveavailability. Other messages ignored.
Message must come from that exact connectedselected/miniiframe at the exact
providerorigin; malformed/wrongorigin/wrongsource/detachedmessages ignored.
No iframe DOM access or providercredential. Not all providerfailures emit such
messages; autoplayblock/networkfailure/non-reportingprovider can stay unknown.
No timeout pretends that unknown means dead, and no automaticretry starts data.

Affectediframe removed and manualRetry/Addnewfeed/OpenonYouTube shown with
textContent and safe11characterID URLs. Recoveryholds prevent unrelatedlist
render/autorenew from restarting failedmini. Retryrecreates only that frame;
othermini frames keep objectidentity. Addnewfeedfocuses existinginput only;
channel add/remove remain browserlocal. Stop clears holds/panels and frames;
staleretry afterstop/selection/removal does nothing. Startdefaults remains an
explicit globalrestart; no private ownerdefaults or serverwrites. Mutation
observer/listener cleanup on pagehide and fresh observer on persistedpageshow; no newsaction triggers playerreload.

Local Chrome320/390/1100 uses interceptednocookiefixtureframes, actualcrossorigin
postMessage, origin/source forgery checks, one-loadhandshakeIDs, endedselected
and errormini/manualretry, unrelatedlistrepaint, Addnewfeedfocus, staleafterstop/
select, XSSliteralextraname, no overflow/errors/outsideAPI/serverwrites. Actual
pixelsinspected. Fixtures prove controls/wiring/layout only, not liveplayback,
currentvideoavailability or providerpolicy. B3separatestorednews/collector gates
unchanged. Collection/sourcehealth/whole-store/operatorcutover remain separate.

The recoveryJS and existing baseJS are served as one combined ESmodule at the
existing brics_streams.js path, not a second request/import. GET and HEAD have
the same security/cache/content-type policy headers. Current emptyHEAD Response
has Content-Length:0 while GET reports full module length; body is empty and
HEAD does not read files. This tests-only revision documents that difference,
not an assertion every entity header is identical.

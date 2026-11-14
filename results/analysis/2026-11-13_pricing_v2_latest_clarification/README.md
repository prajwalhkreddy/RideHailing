# V2 — latest academic clarification reconciliation

Primary: [LATEST_CLARIFICATION_CONTRACT.md](LATEST_CLARIFICATION_CONTRACT.md). Source: `notebooks/plan/Professor_Meeting_Clarifications_DQN_Dynamic_Pricing_Explanation.docx`, sections1–10; full text including tables read. Primary authority for clarified pricing architecture. No claim of independent transcript or equation-number verification. User-supplied implementation directions also apply. Read-only reconciliation plus these five new documents; older results remain historical and unchanged.

**Offer=alpha×P_base; P_max is passenger acceptance ceiling. Pricing is proactive before each30-minute slot, not per request. Passenger-specific fields are not DQN state inputs.** The previous request-level observability argument does not override this instruction. Missing system supply/drop-off context and exact state layout still make current13D incomplete. Rejected contribution0, accepted+allotted revenue; slot aggregation and accepted-unmatched boundary require explicit resolution. Destination vector versus origin-conditioned schedule remains ambiguous, so no output dimension is asserted.

7 numerical/calibration freeze groups and4 architecture decisions remain. The plan is executable after those decisions; it is not falsely labelled ready-to-code with only scalar values missing. Current hybrid generator, physical grid/EV/routing remain; Episode25 exact continuation NO. No model loads, training, fitting, simulation or protected-row analysis.

## State and support verification

CURRENT_VS_V2_ARCHITECTURE.csv maps20 affected components to active symbols, source differences and dependencies. Six previously checked core sources plus replay/routing/operational source fingerprints still match prior audit. Existing supply is available from live fleet, not a pricing-state feature. Existing drop-off infrastructure is strictly lagged six-slot moving average of counts, followed by ordinal quintiles; not a sum-to-one probability vector. Incoming passenger commitments do not automatically include all reposition/charging arrivals.9routing directions are not142destination probabilities.

Weather counts reuse the Jan1–Mar15 restricted cache (8,692,819 source trips) filtered to1.5–75 km, joined many-to-one by pickup hour to existing weather artifacts. Only Jan1–Mar15 weather rows materialized via date filters; March16 excluded. Cache lacks WeatherCode, so this bounded join is for count feasibility only, not raw preparation. Source `coco` is renamed WeatherCode in src/data/weather.py; existing upstream ffill/bfill semantics preserved, not rerun.14actual codes,6,967,155 trips,422observed code×half-hour-of-day groups of672possible:250absent. Minimum total group41, minimum positive35 before final denominator/sign rules. Counts do not equal final fit eligibility. Date/time fields are timezone-naive project timestamps; slot_of_day=2*hour+minute//30; actual slot_start=floor30min.48time-of-day bins available, not automatically selected as academic grouping. Morning/evening examples and older T1–T4 groups are not adopted.

Only Clear1/Rain8/Snowfall15 labels are verified by the existing clean-reference README in this bounded inspection. Other raw codes are preserved without guessing their names; taxonomy normalization requires the existing approved mapping before final group registry. No clustering/merging of categories. Hourly weather can repeat across both half-hours; sample count alone does not measure independent weather exposure.

|WeatherCode|Verified label|Trips|Positive provisional e|Observed half-hours|Minimum group N|Median group N|Maximum group N|Minimum distinct dates/group|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|1|Clear|2109308|1798309|48|7030|48838.5|68256|18|
|2|Raw code; label not verified here|497136|425053|48|179|11584.5|22439|1|
|3|Raw code; label not verified here|3358512|2893822|48|12510|73834.5|126865|29|
|5|Raw code; label not verified here|426746|368567|48|301|8049.5|17970|1|
|7|Raw code; label not verified here|52151|44996|24|141|2364.5|4269|1|
|8|Rain|121186|104368|34|312|3049|7405|1|
|9|Raw code; label not verified here|101832|86813|30|502|2907.5|7073|1|
|12|Raw code; label not verified here|119587|101317|28|364|2679.5|10325|1|
|13|Raw code; label not verified here|18501|15394|12|111|744|4442|1|
|14|Raw code; label not verified here|62047|52369|28|514|1706.5|7111|1|
|15|Snowfall|83209|71647|40|110|863.5|7692|1|
|16|Raw code; label not verified here|12829|9444|30|41|460.5|1221|1|
|17|Raw code; label not verified here|596|510|2|257|298|339|1|
|21|Raw code; label not verified here|3515|3044|2|1550|1757.5|1965|1|

## Count-only half-hour feasibility detail

Each row lists observed slot_index:N:positive_N; slot_index0=00:00,1=00:30,…47=23:30. Missing indices are absent groups, not zeros fabricated into fit data. Positive uses candidate e=r_L/r_P and no price-gap exclusion. No fitting performed.

- Code1: 0:37670:30478, 1:30411:24086, 2:23935:18888, 3:19638:15517, 4:12702:9805, 5:9943:7842, 6:9295:7404, 7:8811:6937, 8:8724:6874, 9:7030:5643, 10:9785:8139, 11:15017:12583, 12:19959:17037, 13:31859:26643, 14:37782:32352, 15:49290:40824, 16:56139:47516, 17:60094:50468, 18:55195:47222, 19:54988:47262, 20:46460:40097, 21:46575:40368, 22:39871:34356, 23:42666:36579, 24:47630:41052, 25:48551:41949, 26:44376:38479, 27:45248:39343, 28:56932:49741, 29:61685:53997, 30:67108:57991, 31:63977:54639, 32:62501:56247, 33:63587:57189, 34:62783:55753, 35:65949:58070, 36:59519:52128, 37:55611:49150, 38:53518:47193, 39:54080:46157, 40:68256:57550, 41:67263:56539, 42:59657:49669, 43:58254:48618, 44:61521:50916, 45:55782:45802, 46:49126:40440, 47:42555:34777
- Code2: 0:20499:16589, 1:16282:13109, 2:7386:5959, 3:6034:4709, 4:9080:7274, 5:7129:5697, 6:197:174, 7:179:160, 8:2511:2006, 9:2134:1733, 10:1373:1127, 11:1816:1551, 12:3080:2587, 13:4912:4011, 14:3930:3438, 15:4982:4157, 16:5654:4837, 17:6276:5310, 18:8820:7794, 19:8543:7581, 20:11876:10510, 21:12314:10995, 22:11436:9961, 23:12464:10831, 24:3773:3394, 25:3726:3372, 26:14092:12508, 27:14507:12935, 28:12415:11073, 29:13541:12071, 30:16272:14637, 31:16087:14261, 32:13549:11858, 33:14448:12531, 34:21134:18569, 35:22439:19618, 36:18665:16131, 37:18888:16006, 38:16679:14065, 39:16339:13853, 40:11733:10049, 41:11291:9745, 42:14926:12505, 43:14664:12244, 44:4017:3361, 45:4474:3650, 46:16542:13346, 47:14028:11171
- Code3: 0:50212:40245, 1:39723:31510, 2:39690:31452, 3:33449:26450, 4:29081:22966, 5:24004:19150, 6:22897:18330, 7:21052:16622, 8:16830:13145, 9:12510:10063, 10:15123:12456, 11:20481:17077, 12:21864:18427, 13:34773:29113, 14:46939:40231, 15:62887:53531, 16:65320:55738, 17:72890:61526, 18:63764:55186, 19:67258:58703, 20:68306:59912, 21:71646:63169, 22:67456:59531, 23:74779:65805, 24:87415:77324, 25:89552:79567, 26:90674:80372, 27:91419:81484, 28:81107:72708, 29:86182:77423, 30:81358:72914, 31:79150:70283, 32:83152:75421, 33:84116:76196, 34:86995:78175, 35:89807:80108, 36:115796:102311, 37:113762:100662, 38:105767:92979, 39:103032:88776, 40:107540:91707, 41:106236:90599, 42:126865:105544, 43:123117:102532, 44:121062:100791, 45:107457:89362, 46:82902:68294, 47:71115:57952
- Code5: 0:9937:7904, 1:8485:6632, 2:6837:5310, 3:5897:4614, 4:410:324, 5:301:242, 6:4651:3476, 7:4157:3046, 8:4588:3365, 9:3432:2647, 10:3017:2498, 11:3307:2815, 12:5208:4365, 13:7439:6248, 14:7500:6430, 15:10326:8768, 16:7269:6385, 17:8752:7641, 18:9718:8512, 19:11035:9616, 20:11647:10206, 21:12617:11059, 22:16229:14408, 23:17535:15459, 24:13133:11773, 25:13608:12208, 26:14694:13088, 27:14049:12647, 28:14442:12965, 29:14684:13223, 30:17970:16248, 31:17868:16141, 32:7142:6484, 33:7614:6949, 34:14556:13106, 35:15371:13684, 36:9146:8168, 37:9111:8144, 38:4897:4336, 39:5148:4428, 40:10882:8957, 41:10662:8698, 42:3905:3034, 43:3766:2858, 44:7226:5809, 45:6965:5675, 46:4954:4136, 47:4659:3838
- Code7: 4:322:269, 5:243:210, 6:167:135, 7:141:117, 8:228:181, 9:276:227, 12:779:679, 13:1331:1170, 20:1856:1612, 21:2176:1861, 22:2189:1868, 23:2300:1980, 28:3059:2684, 29:3389:2984, 30:4223:3794, 31:4269:3801, 32:2429:2287, 33:2602:2406, 38:3459:3025, 39:3428:2897, 42:3811:3053, 43:3682:3006, 44:3256:2630, 45:2536:2120
- Code8: 0:2927:2388, 1:2791:2142, 4:487:386, 5:312:256, 6:1490:1158, 7:1425:1121, 8:1304:1055, 9:901:737, 14:3211:2796, 15:4731:4133, 16:4873:4235, 17:5115:4456, 26:4871:4366, 27:4889:4440, 28:2588:2363, 29:2929:2611, 30:6633:5914, 31:5847:5172, 32:1451:1274, 33:1349:1170, 34:4275:3848, 35:4309:3879, 36:6874:6068, 37:6369:5632, 38:7405:6289, 39:7204:6136, 40:4087:3307, 41:4152:3356, 42:2722:2377, 43:2796:2440, 44:3007:2492, 45:2231:1901, 46:3091:2435, 47:2540:2035
- Code9: 0:3567:2784, 1:2899:2327, 2:2562:2062, 3:2277:1814, 4:2020:1577, 5:1591:1244, 10:502:408, 11:679:584, 12:806:703, 13:1363:1157, 24:2438:2109, 25:2450:2175, 28:2771:2526, 29:2918:2660, 30:2916:2606, 31:2803:2522, 32:5971:5495, 33:6047:5452, 34:3301:2911, 35:3600:3184, 38:2768:2482, 39:2678:2282, 40:6420:5600, 41:5404:4706, 42:7038:5550, 43:7073:5785, 44:3533:3044, 45:3503:2947, 46:4850:4090, 47:5084:4027
- Code12: 0:2639:2157, 1:1898:1530, 2:1247:1014, 3:951:752, 6:364:288, 7:368:301, 8:550:452, 9:601:493, 24:2448:2178, 25:2516:2242, 28:2312:2071, 29:2357:2131, 32:2720:2405, 33:2756:2403, 34:5949:5351, 35:5949:5331, 36:8129:7142, 37:8019:6970, 38:7429:6509, 39:6888:5887, 40:9110:7587, 41:9104:7470, 42:2366:1999, 43:2303:1959, 44:10325:8133, 45:8348:6714, 46:6581:5436, 47:5360:4412
- Code13: 4:174:143, 5:135:119, 6:111:86, 7:118:102, 38:3157:2713, 39:2811:2423, 40:1311:1138, 41:1004:880, 42:4442:3538, 43:4323:3442, 44:484:419, 45:431:391
- Code14: 2:2482:1791, 3:2261:1631, 4:1990:1469, 5:1549:1239, 6:1748:1366, 7:1578:1238, 8:1427:1092, 9:942:764, 10:514:415, 11:641:524, 12:1327:1088, 13:1665:1390, 14:856:750, 15:812:678, 18:3880:3378, 19:4275:3703, 20:2977:2638, 21:3396:3048, 22:5983:5232, 23:7111:6203, 28:2239:1975, 29:2477:2210, 32:2871:2516, 33:3103:2738, 40:1230:1049, 41:1041:897, 42:864:692, 43:808:655
- Code15: 2:183:157, 3:113:101, 4:614:484, 5:489:381, 6:110:88, 7:116:93, 10:380:321, 11:437:371, 12:558:477, 13:800:690, 14:723:637, 15:890:774, 16:837:741, 17:1137:991, 18:2626:2286, 19:3160:2756, 20:179:147, 21:198:167, 22:2077:1788, 23:2169:1882, 24:7541:6380, 25:7692:6586, 26:5690:4857, 27:5822:5011, 28:4012:3413, 29:4007:3397, 30:3500:3133, 31:3571:3115, 32:3097:2863, 33:3155:2869, 34:3840:3227, 35:4015:3340, 36:2989:2603, 37:3013:2595, 38:669:575, 39:814:663, 42:659:563, 43:581:486, 46:401:343, 47:345:296
- Code16: 0:604:490, 1:422:350, 2:140:120, 3:138:121, 4:89:75, 5:74:60, 6:68:51, 7:41:35, 8:228:205, 9:297:254, 16:174:151, 17:173:144, 18:173:146, 19:183:147, 30:646:460, 31:596:434, 32:659:465, 33:567:386, 36:1221:909, 37:1210:915, 38:555:381, 39:548:368, 40:565:370, 41:570:397, 42:497:346, 43:474:343, 44:565:375, 45:490:327, 46:447:315, 47:415:304
- Code17: 8:257:217, 9:339:293
- Code21: 22:1550:1343, 23:1965:1701

## Validation and files

- Required source found/read; explicit decisions distinguished from illustrative EWMA and weather/time examples.
- Safe cache date bounds checked; count sums6,967,155; no March16 orMarch17–31 rows materialized; no weather join duplicates/missing values.
- Source hashes unchanged versus prior audit; only5new requested outputs. No production/runtime tests executed because no implementation changed.
- Outputs: README; LATEST_CLARIFICATION_CONTRACT.md; CURRENT_VS_V2_ARCHITECTURE.csv; V2_IMPLEMENTATION_PLAN.md; REMAINING_NUMERICAL_FREEZES.md.

Source fingerprints:
- Latest DOCX SHA256: `1befbfa76e245d11775b27e7b30728a582e35044ffb886c64ee2a7ebb4133150`
- `src/pricing/passenger_sensitive_v1.py`: `8874b1234f49496721582e43b997532f29bc48768a032be0d971875ce7a65b28`
- `src/simulation/passenger_sensitive_v1.py`: `77e81abaee4c3e4906d778e0858c0cf3ba2b6c811a25f34dc0a0ea7625b2fb30`
- `src/simulation/final_production.py`: `b2cd5371a632e745e1e65dcf9018fa3992942ff2e493caf3ec68b1d422fbaa78`
- `src/dispatch/generation.py`: `ae070a0a2e36341f169e12af98421b0916d9d58bd52ef65b5e61c2a46e3c4abf`
- `src/dispatch/dispatch.py`: `34178812543967eee87b96fa64f637e3d77292c9ad7c2c496b8cd9bcfe70cd62`
- `src/pricing/dqn_contract.py`: `ef9e65e6029ee62504532db9c44fbcb84f5c8f9836056ba0706be01bbcb279ee`
- `src/rl/passenger_sensitive_dqn.py`: `45aa0d662db00b60513b5598afb3fb00648866b1da5cd7e1cac889d05cf18f1c`
- `src/routing/final_state.py`: `5db2dbd8528cbdfadf87d697484f0fb9911e8d4ad81b5cf38ec58aad605749b4`
- `src/simulation/operational_state.py`: `38d803b200a07d78022abc720c9fe955abaeb7b1f53a20c371bb2f038c905e39`

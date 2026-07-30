#OBJECTIVES

    #CORE GAME DATA
    #check unit types from units are valid unit types
    #check races from units are valid races
    #check data values are integers from 0 to... idk 20 or something. IDs should not be 0 (no good reason, just my decision)
    #check that the redundant columns in data in cross reference tables (e.g. race and name for units in unitStates) are good
    #check that the ids that exist in the cross reference tables exist in the main tables (e.g. unitStates unitNumber exists in units)
    #primary key duplication in main and cross reference tables

    #VISUALS
    #visuazlier terrain list is same length (and maybe same names??) as csv.
    #text fields (like notes) are 128 characters or less (u128 in loader). OR use normal python strings.

    #MODs
    #not doing this yet

    #MAPS
    #valid unit types, abilities, terrain types, etc. No more than 1 unit per tile per state
    #REPLAYS
    #these should be generated, so hopefully not a problem. But same checks as maps unless they have different structure

    #AIs
    #have them play a select list of maps against something standard and catch exceptions



#PLAN
    #call (all) loader .py for core game data
    #then check it
    #call loader each map in turn
    #then check it






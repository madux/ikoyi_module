#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Chris.Maduka
#
# Created:     22/05/2019
# Copyright:   (c) Chris.Maduka 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
field_name = """guardian_primary_caregiver
guardian_relationship
father_ethnic_group
mother_ethnic_group
primary_caregiver_occupation
mother_of_child_alive
estimate_mother_age
mother_live_deliveries_count
mother_death_of_live_deliveries_count
father_of_child_alive
father_years_of_formal_education
father_wives_count
wives_order_for_child_mother
father_children_count
child_order_of_index
household_has_smokers
mosquitoes_net_availability
slept_under_net_last_night
usually_sleeps_under_net
place_of_birth
state_of_birth
mode_of_delivery
gestation_age_at_delivery
child_weight_at_birth
child_size_at_birth
was_child_breastfeed
breastfeed_period
father_occupation
mother_occupation,
mother_years_of_formal_education"""

lis = []
for rec in field_name.splitlines():
    lis.append(rec)

    selection = [('Yes', 'Yes'),
             ('No', 'No'),
             ('not_accessed', 'Not Assessed')]

    for tec in range(len(lis)):
        store = '{}=fields.Selection(selection, string="{}", track_visibility="always", readonly=False)'.format(tec,tec)#tec.replace("_", " ").capitalize())
        print store


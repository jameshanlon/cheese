# Create ~/.my.cnf with:
#
#   [client]
#   user=root
#   password=...
#
# before running this to avoid password prompts.
for x in \
alembic_version \
building_types \
cooking_types \
inventory \
kits \
member \
month_feedback \
occupation_types \
post_survey_details \
pre_survey_details \
results \
role \
space_heating_types \
survey_lead_statuses \
surveys \
thermal_image \
user \
user_invite \
user_roles \
wall_construction_types \
wards \
water_heating_types \
year_feedback; \
do
  echo "Exporting $x"
  mysql -e "select * into outfile \"/tmp/mysql-export-$x.csv\" fields terminated by ',' optionally enclosed by '\"' lines terminated by '\n' from cheese.$x"
done

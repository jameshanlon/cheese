for x in \
	member \
	month_feedback \
	post_survey_details \
	pre_survey_details \
	results \
	space_heating_types \
	survey_lead_statuses \
	surveys \
	thermal_image \
	wards \
	year_feedback \
	water_heating_types \
	wall_construction_types \
	building_types cooking_types; do \
  echo "Exporting $x"
  COMMAND="select * into outfile '/tmp/mysql-export-$x.csv' fields terminated by ',' optionally enclosed by '\"' lines terminated by '\n' from cheese.$x;"
  COMMAND="desc cheese.$x"
  mysql -e "select * into outfile \"/tmp/mysql-export-$x.csv\" fields terminated by ',' optionally enclosed by '\"' lines terminated by '\n' from cheese.$x"
done

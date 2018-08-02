# Stitch to Polymer SKU mappings for individual teams.
alabama_team_skus = {
	'1': {'polymer_process_id': 34, 'polymer_product_id': 187},
	'2': {'polymer_process_id': 34, 'polymer_product_id': 187},
	'3': {'polymer_process_id': 34, 'polymer_product_id': 187},
}
valencia_team_skus = {
	'1': {'polymer_process_id': 34, 'polymer_product_id': 31},  # FC Mantuano
	'2': {'polymer_process_id': 119, 'polymer_product_id': 187},  # Delivery Nibs, India
	'3': {'polymer_process_id': 203, 'polymer_product_id': 187},  # Unfoiled Sample Bars, India
}

# EXPORTED: All Stitch to Polymer SKU mappings
stitch_sku_mappings_by_team = {
	1: {'team_skus': alabama_team_skus, 'polymer_userprofile_id': 1},
	2: {'team_skus': valencia_team_skus, 'polymer_userprofile_id': 46}
}

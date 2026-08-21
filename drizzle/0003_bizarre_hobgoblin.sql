CREATE TABLE `food_nutrition` (
	`food_id` text PRIMARY KEY NOT NULL,
	`reference_amount` real NOT NULL,
	`reference_unit` text NOT NULL,
	`calories_kcal` real NOT NULL,
	`protein_grams` real NOT NULL,
	`carbohydrates_grams` real NOT NULL,
	`fat_grams` real NOT NULL,
	`source_provider` text NOT NULL,
	`source_external_id` text NOT NULL,
	`source_url` text NOT NULL,
	`source_retrieved_at` integer NOT NULL,
	`created_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	`updated_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	FOREIGN KEY (`food_id`) REFERENCES `foods`(`id`) ON UPDATE no action ON DELETE cascade,
	CONSTRAINT "food_nutrition_reference_positive" CHECK("food_nutrition"."reference_amount" > 0),
	CONSTRAINT "food_nutrition_calories_non_negative" CHECK("food_nutrition"."calories_kcal" >= 0),
	CONSTRAINT "food_nutrition_protein_non_negative" CHECK("food_nutrition"."protein_grams" >= 0),
	CONSTRAINT "food_nutrition_carbs_non_negative" CHECK("food_nutrition"."carbohydrates_grams" >= 0),
	CONSTRAINT "food_nutrition_fat_non_negative" CHECK("food_nutrition"."fat_grams" >= 0)
);
--> statement-breakpoint
CREATE TABLE `food_package_offers` (
	`id` text PRIMARY KEY NOT NULL,
	`food_id` text NOT NULL,
	`label` text NOT NULL,
	`amount` real NOT NULL,
	`unit` text NOT NULL,
	`price_cents` integer NOT NULL,
	`currency` text DEFAULT 'EUR' NOT NULL,
	`source_type` text NOT NULL,
	`source_provider` text,
	`source_url` text,
	`price_observed_at` integer NOT NULL,
	`created_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	`updated_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	FOREIGN KEY (`food_id`) REFERENCES `foods`(`id`) ON UPDATE no action ON DELETE cascade,
	CONSTRAINT "food_package_offers_amount_positive" CHECK("food_package_offers"."amount" > 0),
	CONSTRAINT "food_package_offers_price_positive" CHECK("food_package_offers"."price_cents" > 0)
);
--> statement-breakpoint
CREATE INDEX `food_package_offers_food_id_idx` ON `food_package_offers` (`food_id`);
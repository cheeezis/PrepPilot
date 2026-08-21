CREATE TABLE `foods` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`normalized_name` text NOT NULL,
	`aliases` text NOT NULL,
	`category` text NOT NULL,
	`default_unit` text NOT NULL,
	`allergens` text NOT NULL,
	`created_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	`updated_at` integer DEFAULT (unixepoch() * 1000) NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `foods_normalized_name_unique` ON `foods` (`normalized_name`);--> statement-breakpoint
CREATE TABLE `ingredient_substitutes` (
	`id` text PRIMARY KEY NOT NULL,
	`recipe_ingredient_id` text NOT NULL,
	`food_id` text NOT NULL,
	`amount` real NOT NULL,
	`unit` text NOT NULL,
	FOREIGN KEY (`recipe_ingredient_id`) REFERENCES `recipe_ingredients`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`food_id`) REFERENCES `foods`(`id`) ON UPDATE no action ON DELETE restrict,
	CONSTRAINT "ingredient_substitutes_amount_positive" CHECK("ingredient_substitutes"."amount" > 0)
);
--> statement-breakpoint
CREATE INDEX `ingredient_substitutes_ingredient_id_idx` ON `ingredient_substitutes` (`recipe_ingredient_id`);--> statement-breakpoint
CREATE TABLE `inventory_items` (
	`id` text PRIMARY KEY NOT NULL,
	`food_id` text NOT NULL,
	`amount` real NOT NULL,
	`unit` text NOT NULL,
	`storage_location` text NOT NULL,
	`expires_at` integer,
	`opened_at` integer,
	`is_staple` integer DEFAULT false NOT NULL,
	`created_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	`updated_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	FOREIGN KEY (`food_id`) REFERENCES `foods`(`id`) ON UPDATE no action ON DELETE restrict,
	CONSTRAINT "inventory_items_amount_positive" CHECK("inventory_items"."amount" > 0)
);
--> statement-breakpoint
CREATE INDEX `inventory_items_food_id_idx` ON `inventory_items` (`food_id`);--> statement-breakpoint
CREATE INDEX `inventory_items_expires_at_idx` ON `inventory_items` (`expires_at`);--> statement-breakpoint
CREATE TABLE `recipe_ingredients` (
	`id` text PRIMARY KEY NOT NULL,
	`recipe_id` text NOT NULL,
	`food_id` text NOT NULL,
	`amount` real NOT NULL,
	`unit` text NOT NULL,
	`requirement` text NOT NULL,
	`preparation` text,
	`position` integer NOT NULL,
	FOREIGN KEY (`recipe_id`) REFERENCES `recipes`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`food_id`) REFERENCES `foods`(`id`) ON UPDATE no action ON DELETE restrict,
	CONSTRAINT "recipe_ingredients_amount_positive" CHECK("recipe_ingredients"."amount" > 0),
	CONSTRAINT "recipe_ingredients_position_non_negative" CHECK("recipe_ingredients"."position" >= 0)
);
--> statement-breakpoint
CREATE INDEX `recipe_ingredients_recipe_id_idx` ON `recipe_ingredients` (`recipe_id`);--> statement-breakpoint
CREATE INDEX `recipe_ingredients_food_id_idx` ON `recipe_ingredients` (`food_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `recipe_ingredients_recipe_position_unique` ON `recipe_ingredients` (`recipe_id`,`position`);--> statement-breakpoint
CREATE TABLE `recipes` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`description` text NOT NULL,
	`servings` integer NOT NULL,
	`prep_minutes` integer NOT NULL,
	`cook_minutes` integer NOT NULL,
	`instructions` text NOT NULL,
	`calories_kcal` real,
	`protein_grams` real,
	`carbohydrates_grams` real,
	`fat_grams` real,
	`dietary_tags` text NOT NULL,
	`source_type` text NOT NULL,
	`source_provider` text,
	`source_external_id` text,
	`source_url` text,
	`source_license` text,
	`source_attribution` text,
	`created_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	`updated_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	CONSTRAINT "recipes_servings_positive" CHECK("recipes"."servings" > 0),
	CONSTRAINT "recipes_prep_minutes_non_negative" CHECK("recipes"."prep_minutes" >= 0),
	CONSTRAINT "recipes_cook_minutes_non_negative" CHECK("recipes"."cook_minutes" >= 0)
);

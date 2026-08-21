CREATE TABLE `shopping_list_items` (
	`id` text PRIMARY KEY NOT NULL,
	`food_id` text NOT NULL,
	`amount` real NOT NULL,
	`unit` text NOT NULL,
	`checked` integer DEFAULT false NOT NULL,
	`created_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	`updated_at` integer DEFAULT (unixepoch() * 1000) NOT NULL,
	FOREIGN KEY (`food_id`) REFERENCES `foods`(`id`) ON UPDATE no action ON DELETE restrict,
	CONSTRAINT "shopping_list_items_amount_positive" CHECK("shopping_list_items"."amount" > 0)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `shopping_list_items_food_id_unique` ON `shopping_list_items` (`food_id`);
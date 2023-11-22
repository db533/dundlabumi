<?php

/**
* Plugin Name: Store Feedback Form with Reviews
* Plugin URI: https://www.example.com/
* Description: Allows logged in users to provide feedback and displays a summary and individual reviews.
* Version: 1.1
* Author: Your Name
* Author URI: https://www.example.com/
**/

// Function to save the feedback
function store_feedback_save() {
    // Similar to previous save function
    // ...
}

// Shortcode to display the feedback form
function store_feedback_form_shortcode() {
    // Similar to previous form shortcode
    // ...
}

// Function to calculate and display the summary of reviews
function store_feedback_summary() {
    $users = get_users();
    $total_rating = $total_recommend = $count = 0;

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);

        if ($rating) {
            $total_rating += $rating;
            $total_recommend += ($recommend === 'yes' ? 1 : 0);
            $count++;
        }
    }

    $average_rating = $count > 0 ? round($total_rating / $count, 1) : 0;
    $recommend_percentage = $count > 0 ? round(($total_recommend / $count) * 100) : 0;

    echo "<p>Average Rating: $average_rating / 5</p>";
    echo "<p>Recommend: $recommend_percentage% of reviewers recommend this store</p>";
}

// Function to display individual reviews
function store_feedback_reviews($sort = 'rating') {
    $args = array(
        'meta_query' => array(
            'relation' => 'AND',
            array(
                'key'     => 'store_rating',
                'compare' => 'EXISTS',
            ),
            array(
                'key'     => 'store_review',
                'compare' => 'EXISTS',
            ),
        ),
        'orderby' => $sort === 'rating' ? 'meta_value_num' : 'registered',
        'order'   => 'DESC',
        'meta_key' => 'store_rating',
    );
    $users = get_users($args);

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $review = get_user_meta($user->ID, 'store_review', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);
        $thumbs_icon = $recommend === 'yes' ? 'thumbs-up.png' : 'thumbs-down.png'; // Replace with actual image URLs

        echo "<div class='review'>";
        echo "<p>Rating: $rating / 5</p>";
        echo "<p>Review: $review</p>";
        echo "<img src='$thumbs_icon' alt='$recommend'>";
        echo "</div>";
    }
}

// Function to calculate and display the summary of reviews
function store_feedback_summary() {
    $users = get_users();
    $total_rating = $total_recommend = $count = 0;

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);

        if ($rating) {
            $total_rating += $rating;
            $total_recommend += ($recommend === 'yes' ? 1 : 0);
            $count++;
        }
    }

    $average_rating = $count > 0 ? round($total_rating / $count, 1) : 0;
    $recommend_percentage = $count > 0 ? round(($total_recommend / $count) * 100) : 0;

    echo "<p>Average Rating: $average_rating / 5</p>";
    echo "<p>Recommend: $recommend_percentage% of reviewers recommend this store</p>";
}

// Function to display individual reviews
function store_feedback_reviews($sort = 'rating') {
    $args = array(
        'meta_query' => array(
            'relation' => 'AND',
            array(
                'key'     => 'store_rating',
                'compare' => 'EXISTS',
            ),
            array(
                'key'     => 'store_review',
                'compare' => 'EXISTS',
            ),
        ),
        'orderby' => $sort === 'rating' ? 'meta_value_num' : 'registered',
        'order'   => 'DESC',
        'meta_key' => 'store_rating',
    );
    $users = get_users($args);

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $review = get_user_meta($user->ID, 'store_review', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);
        $thumbs_icon = $recommend === 'yes' ? 'thumbs-up.png' : 'thumbs-down.png'; // Replace with actual image URLs

        echo "<div class='review'>";
        echo "<p>Rating: $rating / 5</p>";
        echo "<p>Review: $review</p>";
        echo "<img src='$thumbs_icon' alt='$recommend'>";
        echo "</div>";
    }
}

// Shortcode to display the summary and reviews
function store_feedback_display_shortcode($atts) {
    ob_start();

    $atts = shortcode_atts( array(
        'sort' => 'rating',
    ), $atts );

    store_feedback_summary();
    store_feedback_reviews($atts['sort']);

    return ob_get_clean();
}

add_shortcode('store_feedback_form', 'store_feedback_form_shortcode');
add_shortcode('store_feedback_display', 'store_feedback_display_shortcode');

// Register AJAX actions if needed
add_action('wp_ajax_store_feedback_save', 'store_feedback_save');
add_action('wp_ajax_nopriv_store_feedback_save', 'store_feedback_save');

?>

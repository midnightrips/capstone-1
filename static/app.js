const $favBtns = $('.favorite-btn');

async function toggleFavorite(e) {
    e.preventDefault();
    e.stopPropagation();

    const $btn = $(e.currentTarget);
    const $starIcon = $btn.find('.star');
    const gameId = $btn.data('game-id'); // Use a data attribute for the game ID

    try {
        const response = await axios.post(`/games/add-like/${gameId}`);

        if (response.data.favorited) {
            $starIcon.removeClass('bi-star unfilled').addClass('bi-star-fill filled').css('color', 'gold');
        } else {
            $starIcon.removeClass('bi-star-fill filled').addClass('bi-star unfilled').css('color', 'grey');
        }
    } catch (err) {
        console.error('Error toggling favorite status:', err);
    }
}

$favBtns.on('click', toggleFavorite);